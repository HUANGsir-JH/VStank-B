"""
集成测试 - 验证多人游戏模块与主游戏的集成
"""

import sys
import os

# 添加父目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """测试所有模块导入"""
    print("🔍 测试模块导入...")
    
    try:
        # 测试主游戏模块
        import tank_sprites
        print("  ✅ tank_sprites 导入成功")
        
        import game_views
        print("  ✅ game_views 导入成功")
        
        import maps
        print("  ✅ maps 导入成功")
        
        # 测试多人游戏模块
        from multiplayer import udp_discovery
        print("  ✅ multiplayer.udp_discovery 导入成功")
        
        from multiplayer import udp_host
        print("  ✅ multiplayer.udp_host 导入成功")
        
        from multiplayer import udp_client
        print("  ✅ multiplayer.udp_client 导入成功")
        
        from multiplayer import udp_messages
        print("  ✅ multiplayer.udp_messages 导入成功")
        
        from multiplayer import network_views
        print("  ✅ multiplayer.network_views 导入成功")
        
        print("  🎉 所有模块导入成功！")
        return True
        
    except Exception as e:
        print(f"  ❌ 模块导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_game_integration():
    """测试游戏集成"""
    print("\n🎮 测试游戏集成...")
    
    try:
        # 测试模块导入（不创建视图对象）
        import game_views
        print("  ✅ game_views 模块导入成功")
        
        import multiplayer.network_views
        print("  ✅ multiplayer.network_views 模块导入成功")
        
        # 测试坦克类扩展
        from tank_sprites import Tank
        tank = Tank(None, 0.5, 100, 100)
        tank.player_id = "test_player"
        print(f"  ✅ Tank 扩展成功，player_id: {tank.player_id}")
        
        # 测试子弹发射
        bullet = tank.shoot(0.0)
        if bullet:
            print(f"  ✅ 子弹发射成功，所有者: {bullet.owner.player_id}")
        
        print("  🎉 游戏集成测试成功！")
        return True
        
    except Exception as e:
        print(f"  ❌ 游戏集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_network_functionality():
    """测试网络功能"""
    print("\n🌐 测试网络功能...")
    
    try:
        from multiplayer.udp_messages import MessageFactory
        
        # 创建测试消息
        msg = MessageFactory.create_room_advertise("测试房间", 1, 4)
        data = msg.to_bytes()
        print(f"  ✅ 消息创建成功，大小: {len(data)} 字节")
        
        # 测试房间发现
        from multiplayer.udp_discovery import RoomAdvertiser
        advertiser = RoomAdvertiser()
        print("  ✅ RoomAdvertiser 创建成功")
        
        # 测试主机
        from multiplayer.udp_host import GameHost
        host = GameHost()
        print("  ✅ GameHost 创建成功")
        
        # 测试客户端
        from multiplayer.udp_client import GameClient
        client = GameClient()
        print("  ✅ GameClient 创建成功")
        
        print("  🎉 网络功能测试成功！")
        return True
        
    except Exception as e:
        print(f"  ❌ 网络功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("🚀 坦克动荡 - 集成测试")
    print("=" * 50)
    
    tests = [
        ("模块导入", test_imports),
        ("游戏集成", test_game_integration),
        ("网络功能", test_network_functionality)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 集成测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有集成测试通过！多人游戏模块已成功集成到主游戏中。")
        print("\n📋 下一步:")
        print("1. 运行 'python main.py' 启动游戏")
        print("2. 选择 '多人联机' 模式")
        print("3. 创建或加入房间开始多人游戏")
    else:
        print("⚠️ 部分集成测试失败，请检查上述错误信息。")


if __name__ == "__main__":
    main()
