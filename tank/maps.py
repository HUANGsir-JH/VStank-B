import random

# --- 常量 ---
# 这些值最好与 game_views.py 中的常量保持一致或从共享配置中读取
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
WALL_THICKNESS_FOR_PLAYER_START = 10 # 用于计算玩家起始位置的墙壁厚度 (与 game_views.py 一致)

# 游戏区域边界 (与 game_views.py 一致)
TOP_UI_PANEL_HEIGHT = 30
BOTTOM_UI_PANEL_HEIGHT = 60
GAME_AREA_BOTTOM_Y = BOTTOM_UI_PANEL_HEIGHT
GAME_AREA_TOP_Y = SCREEN_HEIGHT - TOP_UI_PANEL_HEIGHT

# 坦克相关尺寸 (需要与 tank_sprites.py 和 game_views.py 中的缩放一致)
# 假设坦克原始宽度为86, 缩放为0.65
TANK_UNSCALED_WIDTH = 86
PLAYER_SCALE = 0.65
TANK_ACTUAL_WIDTH = TANK_UNSCALED_WIDTH * PLAYER_SCALE # 约 55.9
TANK_PASSAGE_BUFFER = TANK_ACTUAL_WIDTH + 15 # 确保坦克能通过的最小空隙，比坦克宽一些

# 玩家起始位置 (与 game_views.py 一致)
P1_START_X = WALL_THICKNESS_FOR_PLAYER_START * 3
P2_START_X = SCREEN_WIDTH - (WALL_THICKNESS_FOR_PLAYER_START * 3)

# 地图障碍物可生成的X轴范围
MAP_MIN_X = P1_START_X + TANK_ACTUAL_WIDTH # 坦克初始位置右侧开始
MAP_MAX_X = P2_START_X - TANK_ACTUAL_WIDTH # 坦克初始位置左侧结束

# 地图墙壁的默认厚度 (可以根据地图设计调整)
DEFAULT_MAP_WALL_THICKNESS = 20

# --- 地图定义 ---
# 每张地图是一个墙壁列表，每个墙壁是一个元组: (center_x, center_y, width, height)

# 地图1: 中间两条横向墙壁，中间留有较大开口
# 开口宽度约为 SCREEN_WIDTH * 0.3 = 384 (原 SCREEN_WIDTH * 0.2 = 256)
LEFT_WALL_END_X_MAP1 = SCREEN_WIDTH * 0.35  # X坐标 448 (原 0.4 -> 512)
RIGHT_WALL_START_X_MAP1 = SCREEN_WIDTH * 0.65 # X坐标 832 (原 0.6 -> 768)

MAP_1_WALLS = [
    # 左侧横向墙 (从 MAP_MIN_X 到 LEFT_WALL_END_X_MAP1)
    ( MAP_MIN_X + (LEFT_WALL_END_X_MAP1 - MAP_MIN_X) / 2, SCREEN_HEIGHT / 2, LEFT_WALL_END_X_MAP1 - MAP_MIN_X, DEFAULT_MAP_WALL_THICKNESS),
    # 右侧横向墙 (从 RIGHT_WALL_START_X_MAP1 到 MAP_MAX_X)
    ( RIGHT_WALL_START_X_MAP1 + (MAP_MAX_X - RIGHT_WALL_START_X_MAP1) / 2, SCREEN_HEIGHT / 2, MAP_MAX_X - RIGHT_WALL_START_X_MAP1, DEFAULT_MAP_WALL_THICKNESS),
    
    # 上下各增加一些垂直短墙，增加复杂度
    # 左上垂直墙 (更靠左侧区域的中间)
    ( MAP_MIN_X + (LEFT_WALL_END_X_MAP1 - MAP_MIN_X) * 0.3, GAME_AREA_BOTTOM_Y + (GAME_AREA_TOP_Y - GAME_AREA_BOTTOM_Y) * 0.25, DEFAULT_MAP_WALL_THICKNESS, (GAME_AREA_TOP_Y - GAME_AREA_BOTTOM_Y) * 0.2), # 缩小长度
    # 右上垂直墙 (更靠右侧区域的中间)
    ( MAP_MAX_X - (MAP_MAX_X - RIGHT_WALL_START_X_MAP1) * 0.3, GAME_AREA_BOTTOM_Y + (GAME_AREA_TOP_Y - GAME_AREA_BOTTOM_Y) * 0.25, DEFAULT_MAP_WALL_THICKNESS, (GAME_AREA_TOP_Y - GAME_AREA_BOTTOM_Y) * 0.2), # 缩小长度
    # 左下垂直墙
    ( MAP_MIN_X + (LEFT_WALL_END_X_MAP1 - MAP_MIN_X) * 0.7, GAME_AREA_TOP_Y - (GAME_AREA_TOP_Y - GAME_AREA_BOTTOM_Y) * 0.25, DEFAULT_MAP_WALL_THICKNESS, (GAME_AREA_TOP_Y - GAME_AREA_BOTTOM_Y) * 0.2), # 缩小长度
    # 右下垂直墙
    ( MAP_MAX_X - (MAP_MAX_X - RIGHT_WALL_START_X_MAP1) * 0.7, GAME_AREA_TOP_Y - (GAME_AREA_TOP_Y - GAME_AREA_BOTTOM_Y) * 0.25, DEFAULT_MAP_WALL_THICKNESS, (GAME_AREA_TOP_Y - GAME_AREA_BOTTOM_Y) * 0.2), # 缩小长度
    # 在中间通道增加两个错开的短竖墙 (S型绕行)
    ( (LEFT_WALL_END_X_MAP1 + SCREEN_WIDTH / 2) / 2, SCREEN_HEIGHT / 2 - 60, DEFAULT_MAP_WALL_THICKNESS, 120), # 左上竖墙
    ( (RIGHT_WALL_START_X_MAP1 + SCREEN_WIDTH / 2) / 2, SCREEN_HEIGHT / 2 + 60, DEFAULT_MAP_WALL_THICKNESS, 120), # 右下竖墙
]

# 地图2: 对称的 "H" 型障碍
H_VERTICAL_BAR_HEIGHT = SCREEN_HEIGHT * 0.5
# H型墙壁的关键坐标
X_LEFT_H_WALL = MAP_MIN_X + (SCREEN_WIDTH / 2 - MAP_MIN_X) / 2
X_RIGHT_H_WALL = MAP_MAX_X - (MAP_MAX_X - SCREEN_WIDTH / 2) / 2
Y_CENTER_H_WALL = SCREEN_HEIGHT / 2
Y_H_TOP = Y_CENTER_H_WALL - H_VERTICAL_BAR_HEIGHT / 2
Y_H_BOTTOM = Y_CENTER_H_WALL + H_VERTICAL_BAR_HEIGHT / 2
# H型外部延伸墙参数
OUTER_EXTENSION_LENGTH = 150 
# H型上下开口障碍的原宽度，现在用作高度
H_OPENING_OBSTACLE_FORMER_WIDTH = 150

MAP_2_WALLS = [
    # 左侧竖条
    (X_LEFT_H_WALL, Y_CENTER_H_WALL, DEFAULT_MAP_WALL_THICKNESS, H_VERTICAL_BAR_HEIGHT),
    # 右侧竖条
    (X_RIGHT_H_WALL, Y_CENTER_H_WALL, DEFAULT_MAP_WALL_THICKNESS, H_VERTICAL_BAR_HEIGHT),
    # 中间横条
    (SCREEN_WIDTH / 2, Y_CENTER_H_WALL, X_RIGHT_H_WALL - X_LEFT_H_WALL - DEFAULT_MAP_WALL_THICKNESS, DEFAULT_MAP_WALL_THICKNESS), # 宽度调整为精确连接
    # 在H的上下开口处增加短竖墙 (原为横墙)
    (SCREEN_WIDTH / 2, Y_CENTER_H_WALL - (H_VERTICAL_BAR_HEIGHT / 2) - DEFAULT_MAP_WALL_THICKNESS - 20, DEFAULT_MAP_WALL_THICKNESS, H_OPENING_OBSTACLE_FORMER_WIDTH), # 上部竖直障碍
    (SCREEN_WIDTH / 2, Y_CENTER_H_WALL + (H_VERTICAL_BAR_HEIGHT / 2) + DEFAULT_MAP_WALL_THICKNESS + 20, DEFAULT_MAP_WALL_THICKNESS, H_OPENING_OBSTACLE_FORMER_WIDTH), # 下部竖直障碍
    # 在H的四个外角增加横向延伸墙
    # 左上外延
    (X_LEFT_H_WALL - DEFAULT_MAP_WALL_THICKNESS / 2 - OUTER_EXTENSION_LENGTH / 2, 
     Y_H_TOP,
     OUTER_EXTENSION_LENGTH, DEFAULT_MAP_WALL_THICKNESS),
    # 右上外延
    (X_RIGHT_H_WALL + DEFAULT_MAP_WALL_THICKNESS / 2 + OUTER_EXTENSION_LENGTH / 2,
     Y_H_TOP,
     OUTER_EXTENSION_LENGTH, DEFAULT_MAP_WALL_THICKNESS),
    # 左下外延
    (X_LEFT_H_WALL - DEFAULT_MAP_WALL_THICKNESS / 2 - OUTER_EXTENSION_LENGTH / 2,
     Y_H_BOTTOM,
     OUTER_EXTENSION_LENGTH, DEFAULT_MAP_WALL_THICKNESS),
    # 右下外延
    (X_RIGHT_H_WALL + DEFAULT_MAP_WALL_THICKNESS / 2 + OUTER_EXTENSION_LENGTH / 2,
     Y_H_BOTTOM,
     OUTER_EXTENSION_LENGTH, DEFAULT_MAP_WALL_THICKNESS),
]

# 地图3: 四个角落的小障碍块 + 中间一个旋转的十字
MAP_3_WALLS = [
    # 左上
    (MAP_MIN_X + 40, GAME_AREA_BOTTOM_Y + 50, 80, 80),
    # 右上
    (MAP_MAX_X - 40, GAME_AREA_BOTTOM_Y + 50, 80, 80),
    # 左下
    (MAP_MIN_X + 40, GAME_AREA_TOP_Y - 50, 80, 80),
    # 右下
    (MAP_MAX_X - 40, GAME_AREA_TOP_Y - 50, 80, 80),
    # 中间十字 (确保在X轴限制内)
    (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, DEFAULT_MAP_WALL_THICKNESS, 400), # 竖条 (高400)
    (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, 400, DEFAULT_MAP_WALL_THICKNESS), # 横条 (宽400)
    # 新增两个垂直短墙 (对角线对称，贴紧边界)
    (SCREEN_WIDTH * 0.25, GAME_AREA_TOP_Y - 100, DEFAULT_MAP_WALL_THICKNESS, 200), # 左上延展 (贴顶)
    (SCREEN_WIDTH * 0.75, GAME_AREA_BOTTOM_Y + 100, DEFAULT_MAP_WALL_THICKNESS, 200), # 右下延展 (贴底)
]

ALL_MAP_LAYOUTS = [MAP_1_WALLS, MAP_2_WALLS, MAP_3_WALLS]

def get_random_map_layout():
    """随机选择并返回一个地图布局数据。"""
    return random.choice(ALL_MAP_LAYOUTS) # 恢复随机选择
    # return MAP_1_WALLS # 固定返回地图1进行测试
    # return MAP_2_WALLS # 固定返回地图2进行测试
    # return MAP_3_WALLS # 固定返回地图3进行测试

def get_map_constants():
    """返回地图设计时可能需要的常量，方便GameView使用。"""
    return {
        "map_min_x": MAP_MIN_X,
        "map_max_x": MAP_MAX_X,
        "game_area_bottom_y": GAME_AREA_BOTTOM_Y,
        "game_area_top_y": GAME_AREA_TOP_Y,
        "tank_passage_buffer": TANK_PASSAGE_BUFFER,
        "default_map_wall_thickness": DEFAULT_MAP_WALL_THICKNESS
    }

if __name__ == '__main__':
    # 测试代码
    print(f"Tank actual width: {TANK_ACTUAL_WIDTH}")
    print(f"Tank passage buffer: {TANK_PASSAGE_BUFFER}")
    print(f"Map generatable X range: [{MAP_MIN_X}, {MAP_MAX_X}]")
    print(f"Map generatable Y range: [{GAME_AREA_BOTTOM_Y}, {GAME_AREA_TOP_Y}]")

    selected_map = get_random_map_layout()
    print("\nSelected map layout:")
    for wall in selected_map:
        print(wall)
    
    constants = get_map_constants()
    print("\nMap Constants:")
    for key, value in constants.items():
        print(f"{key}: {value}")
