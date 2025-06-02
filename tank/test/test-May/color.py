import arcade

class Bullet(arcade.Sprite):
    def __init__(self, position_x, position_y, change_x, change_y, color):
        # 调用父类的初始化方法
        super().__init__()

        # 设置子弹的位置
        self.center_x = position_x
        self.center_y = position_y

        # 设置子弹的速度
        self.change_x = change_x
        self.change_y = change_y

        # 设置子弹的颜色
        self.color = color

        # 创建一个简单的矩形形状作为子弹
        self.width = 10
        self.height = 20

    def update(self, delta_time):
        # 更新子弹的位置
        self.center_x += self.change_x
        self.center_y += self.change_y

# 初始化窗口
window = arcade.open_window(800, 600, "Bullet Color Example")

# 创建一个红色子弹
bullet = Bullet(400, 300, 0, 5, arcade.color.RED)

# 将子弹添加到精灵列表中
bullet_list = arcade.SpriteList()
bullet_list.append(bullet)

# 游戏主循环
def on_draw():
    arcade.start_render()
    bullet_list.draw()

bullet_list.update()

arcade.schedule(bullet_list.update, 1/60)  # 每秒更新60次
arcade.run()