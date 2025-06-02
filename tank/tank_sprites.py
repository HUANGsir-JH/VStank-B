import arcade
import math
import os
import pymunk # <--- 添加Pymunk导入

# --- 常量 ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720 # 同上

PLAYER_MOVEMENT_SPEED = 5
PLAYER_TURN_SPEED = 5  # 度/帧
PLAYER_SCALE = 0.8  # 坦克图片的缩放比例


# 获取 tank_sprites.py 文件所在的目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# PLAYER_IMAGE_PATH_GREEN = os.path.join(BASE_DIR, "tank-img", "tanks_tankGreen1.png")
# PLAYER_IMAGE_PATH_DESERT = os.path.join(BASE_DIR, "tank-img", "tanks_tankDesert1.png")
# PLAYER_IMAGE_PATH_BLUE = os.path.join(BASE_DIR, "tank-img", "tanks_tankNavy1.png")
# PLAYER_IMAGE_PATH_GREY = os.path.join(BASE_DIR, "tank-img", "tanks_tankGrey1.png")

PLAYER_IMAGE_PATH_GREEN = os.path.join(BASE_DIR, "tank-img", "green_tank.png")
PLAYER_IMAGE_PATH_DESERT = os.path.join(BASE_DIR, "tank-img", "yellow_tank.png")
PLAYER_IMAGE_PATH_BLUE = os.path.join(BASE_DIR, "tank-img", "blue_tank.png")
PLAYER_IMAGE_PATH_GREY = os.path.join(BASE_DIR, "tank-img", "grey_tank.png")

# 音效文件路径
EXPLOSION_SOUND = os.path.join(BASE_DIR, "tank_voice", "explosion.wav")

# Pymunk碰撞类型常量
COLLISION_TYPE_BULLET = 1
COLLISION_TYPE_WALL = 2
COLLISION_TYPE_TANK = 3

class Tank(arcade.Sprite):
    """ 坦克类 """
    def __init__(self, image_file, scale, center_x, center_y, max_speed=PLAYER_MOVEMENT_SPEED, turn_speed_degrees=PLAYER_TURN_SPEED):
        # 存储图片文件路径，供后续使用
        self.tank_image_file = image_file

        # 检查图片文件是否存在
        if image_file and os.path.exists(image_file):
            super().__init__(image_file, scale)
        elif image_file: # 文件路径提供了，但未找到
            print(f"警告: 坦克图片 '{image_file}' 未找到。将使用红色占位符。")
            super().__init__(scale=scale)
            tank_width = int(50 * scale)
            self.texture = arcade.make_soft_square_texture(tank_width, arcade.color.RED, outer_alpha=255)
        else: # image_file 为 None
            print(f"信息: 未提供坦克图片。将使用蓝色占位符。")
            super().__init__(scale=scale)
            tank_width = int(50 * scale)
            self.texture = arcade.make_soft_square_texture(tank_width, arcade.color.BLUE, outer_alpha=255)

        self.angle = 0
        self.center_x = center_x
        self.center_y = center_y
        self.speed = 0
        self.angle_speed = 0
        self.max_speed = max_speed
        self.turn_speed_degrees = turn_speed_degrees
        self.health = 5
        self.max_health = 5

        # 玩家标识（用于网络游戏）
        self.player_id = None

        # 射击冷却时间属性
        self.last_shot_time = -1.0 # 上次射击的时间（初始化为负值，确保第一次射击可以成功）
        self.shot_cooldown = 0.4 # 射击冷却时间 (秒)

        self.pymunk_body = None
        self.pymunk_shape = None
        mass = 10

        if self.texture and hasattr(self.texture, 'image') and self.texture.image:
            unscaled_width = self.texture.image.width
            unscaled_height = self.texture.image.height
        elif self.texture:
            unscaled_width = self.texture.width
            unscaled_height = self.texture.height
            if isinstance(unscaled_width, tuple):
                unscaled_width = unscaled_width[0]
            if isinstance(unscaled_height, tuple):
                unscaled_height = unscaled_height[0]
        else:
            unscaled_width = int(50)
            unscaled_height = int(60)


        try:
            calc_unscaled_width = float(unscaled_width[0] if isinstance(unscaled_width, tuple) else unscaled_width)
            calc_unscaled_height = float(unscaled_height[0] if isinstance(unscaled_height, tuple) else unscaled_height)
        except Exception as e:
            print(f"ERROR converting unscaled dimensions: {e}. Falling back to defaults.")
            calc_unscaled_width = 50.0
            calc_unscaled_height = 60.0

        current_scale_for_pymunk = self.scale
        if isinstance(self.scale, tuple):
            current_scale_for_pymunk = self.scale[0]

        # 再次微调Pymunk形状的尺寸，使其略小于缩放后的图片尺寸，以更精确地贴合坦克主体
        # 尝试将尺寸缩小到缩放后图片尺寸的90%
        # 再次微调Pymunk形状的尺寸，使其略小于缩放后的图片尺寸，以更精确地贴合坦克主体
        # 尝试将尺寸缩小到缩放后图片尺寸的80%
        # 坦克的视觉宽度对应图片的宽度 (calc_unscaled_width)
        # 坦克的视觉高度对应图片的高度 (calc_unscaled_height)

        # Pymunk形状的局部X轴尺寸 (对应视觉高度)
        half_x_dim_for_pymunk_shape = (calc_unscaled_height * current_scale_for_pymunk ) / 2
        # Pymunk形状的局部Y轴尺寸 (对应视觉宽度)
        half_y_dim_for_pymunk_shape = (calc_unscaled_width * current_scale_for_pymunk ) / 2

        # Pymunk的Poly形状顶点定义，对调尺寸以匹配视觉方向
        vertices = [(-half_x_dim_for_pymunk_shape, -half_y_dim_for_pymunk_shape),
                    (half_x_dim_for_pymunk_shape, -half_y_dim_for_pymunk_shape),
                    (half_x_dim_for_pymunk_shape, half_y_dim_for_pymunk_shape),
                    (-half_x_dim_for_pymunk_shape, half_y_dim_for_pymunk_shape)]
        moment = pymunk.moment_for_poly(mass, vertices)

        self.pymunk_body = pymunk.Body(mass, moment)
        self.pymunk_body.position = center_x, center_y
        # 将Arcade的0度（向上）转换为Pymunk的math.pi/2（向上）
        self.pymunk_body.angle = math.radians(90 - self.angle)
        # 为坦克启用连续碰撞检测 (CCD)
        self.pymunk_body.linear_velocity_threshold = 0.1 # 设置一个小的阈值以启用CCD，防止高速穿模

        self.pymunk_shape = pymunk.Poly(self.pymunk_body, vertices)
        self.pymunk_shape.elasticity = 0.0 # 碰撞后立即停止，无反弹
        self.pymunk_shape.friction = 1   # 1表示高摩擦力
        self.pymunk_shape.collision_type = COLLISION_TYPE_TANK
        self.pymunk_shape.collision_bias = 0.01 # 增加碰撞偏置，防止重叠

        self.pymunk_body.damping = 1 # 线性阻尼，越大越快停止移动
        self.pymunk_body.angular_damping = 1 # 角阻尼，越大越快停止旋转
        self.pymunk_body.sprite = self

    def take_damage(self, amount):
        self.health -= amount
        if self.health < 0:
            self.health = 0
        print(f"Tank at ({self.center_x:.0f},{self.center_y:.0f}) took {amount} damage, health: {self.health}")

    def is_alive(self):
        return self.health > 0

    def update(self, delta_time: float = 1/60):
        pass

    def sync_with_pymunk_body(self):
        if self.pymunk_body:
            self.center_x = self.pymunk_body.position.x
            self.center_y = self.pymunk_body.position.y
            # 将Pymunk的math.pi/2（向上）转换为Arcade的0度（向上）
            self.angle = 90 - math.degrees(self.pymunk_body.angle)


    def shoot(self, current_time): # 接收当前时间参数
        # 检查射击冷却时间
        if current_time - self.last_shot_time < self.shot_cooldown:
            return None # 未冷却，不射击

        # 更新上次射击时间
        self.last_shot_time = current_time

        # 播放射击音效（仅在非测试环境下）
        try:
            if os.path.exists(EXPLOSION_SOUND):
                arcade.play_sound(arcade.load_sound(EXPLOSION_SOUND))
        except Exception as e:
            # 在测试环境中可能没有音频设备，忽略音效错误
            pass

        IMAGE_BARREL_DIRECTION_OFFSET = 0
        actual_bullet_angle = IMAGE_BARREL_DIRECTION_OFFSET - self.angle

        bullet_color = arcade.color.YELLOW_ORANGE

        if hasattr(self, 'tank_image_file') and self.tank_image_file:
            path = self.tank_image_file.lower()
            if 'green' in path: bullet_color = (0, 255, 0)
            elif 'desert' in path: bullet_color = (255, 165, 0)
            elif 'grey' in path: bullet_color = (128, 128, 128)
            elif 'blue' in path: bullet_color = (0, 0, 128)

        # 定义子弹半径和速度
        BULLET_RADIUS = 4
        BULLET_SPEED_MAGNITUDE = 16

        bullet = Bullet(radius=BULLET_RADIUS,
                       owner=self,
                       tank_center_x=self.center_x,
                       tank_center_y=self.center_y,
                       actual_emission_angle_degrees=actual_bullet_angle,
                       speed_magnitude=BULLET_SPEED_MAGNITUDE,
                       color=bullet_color)
        return bullet

# --- 子弹类 ---
class Bullet(arcade.SpriteCircle):
    """ 子弹类 """
    def __init__(self, radius, owner, tank_center_x, tank_center_y, actual_emission_angle_degrees, speed_magnitude, color):
        super().__init__(radius, color)
        self.radius = radius

        self.center_x = tank_center_x
        self.center_y = tank_center_y

        self.owner = owner
        self.angle = actual_emission_angle_degrees
        self.bounce_count = 0
        self.max_bounces = 3

        self.pymunk_body = None
        self.pymunk_shape = None
        mass = 0.001

        moment = pymunk.moment_for_circle(mass, 0, self.radius, (0,0))

        self.pymunk_body = pymunk.Body(mass, moment)
        # 为子弹启用连续碰撞检测 (CCD)
        # 将阈值设置为子弹的实际速度大小，确保CCD始终启用
        self.pymunk_body.linear_velocity_threshold = 0.1

        barrel_offset = 25 * PLAYER_SCALE
        emission_angle_rad = math.radians(actual_emission_angle_degrees)

        self.pymunk_body.position = (
            tank_center_x - barrel_offset * math.sin(emission_angle_rad),
            tank_center_y + barrel_offset * math.cos(emission_angle_rad)
        )
        self.pymunk_body.angle = math.radians(actual_emission_angle_degrees)

        pymunk_initial_speed = speed_magnitude * 60
        vx = -pymunk_initial_speed * math.sin(self.pymunk_body.angle)
        vy = pymunk_initial_speed * math.cos(self.pymunk_body.angle)
        self.pymunk_body.velocity = (vx, vy)
        self.pymunk_body.damping = 1.0

        self.pymunk_shape = pymunk.Circle(self.pymunk_body, self.radius, (0,0))
        self.pymunk_shape.friction = 0.1 # 0.1表示低摩擦力
        self.pymunk_shape.elasticity = 1
        self.pymunk_shape.collision_type = COLLISION_TYPE_BULLET
        self.pymunk_body.sprite = self

        self.sync_with_pymunk_body()

    def update(self, delta_time: float = 1/60):
        pass

    def sync_with_pymunk_body(self):
        if self.pymunk_body:
            self.center_x = self.pymunk_body.position.x
            self.center_y = self.pymunk_body.position.y
            self.angle = math.degrees(self.pymunk_body.angle)
