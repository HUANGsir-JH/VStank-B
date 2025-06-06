import arcade
from game_views import MainMenu # 从 game_views.py 导入 MainMenu 视图
from fps_config import set_fps_config, apply_fps_to_window
# 其他导入可以根据需要添加，例如常量等

# --- 常量 ---
# 这些常量如果只在 main.py 中使用，可以保留在这里
# 如果 game_views.py 或 tank_sprites.py 也需要它们，最好定义在一个共享的 constants.py 文件中
# 或者在各自文件中定义（如果它们特定于该文件）
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCREEN_TITLE = "坦克动荡"

def main():
    """ 主函数，程序的入口点 """
    # 设置统一的FPS配置
    fps_config = set_fps_config("high_performance")  # 使用高性能模式

    # 创建窗口并应用FPS设置
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    apply_fps_to_window(window)

    # 显示主菜单
    main_menu_view = MainMenu()
    window.show_view(main_menu_view)
    arcade.run()

if __name__ == "__main__":
    main()
