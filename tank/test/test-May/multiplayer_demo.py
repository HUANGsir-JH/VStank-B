"""
多人游戏演示程序

用于演示多人游戏功能的简单启动器
"""

import arcade
import sys
import os

# 添加父目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multiplayer.network_views import RoomBrowserView


class MultiplayerDemoWindow(arcade.Window):
    """多人游戏演示窗口"""
    
    def __init__(self):
        super().__init__(1280, 720, "坦克动荡 - 多人游戏演示")
        
        # 直接显示房间浏览视图
        room_browser = RoomBrowserView()
        self.show_view(room_browser)


def main():
    """主函数"""
    print("🎮 坦克动荡 - 多人游戏演示")
    print("=" * 40)
    print("这是一个多人游戏功能的演示程序")
    print()
    print("操作说明:")
    print("- ↑↓ 选择房间")
    print("- Enter 加入房间")
    print("- C 创建房间")
    print("- Esc 退出")
    print()
    print("网络要求:")
    print("- 确保防火墙允许UDP端口12345-12346")
    print("- 所有设备需在同一局域网内")
    print()
    print("正在启动演示程序...")
    
    try:
        window = MultiplayerDemoWindow()
        arcade.run()
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        input("按回车键退出...")


if __name__ == "__main__":
    main()
