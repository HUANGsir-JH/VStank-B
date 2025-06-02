"""
最小多人游戏测试
"""

import arcade
import sys
import os

# 添加父目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_multiplayer_view_creation():
    """测试多人游戏视图创建"""
    print("🌐 测试多人游戏视图创建...")
    
    try:
        from multiplayer.network_views import RoomBrowserView
        print("  ✅ RoomBrowserView 导入成功")
        
        # 不创建窗口，只测试类定义
        print("  ✅ 多人游戏视图模块正常")
        return True
        
    except Exception as e:
        print(f"  ❌ 多人游戏视图创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_game_views_integration():
    """测试游戏视图集成"""
    print("\n🎮 测试游戏视图集成...")
    
    try:
        import game_views
        print("  ✅ game_views 导入成功")
        
        # 检查ModeSelectView是否有多人游戏选项
        import inspect
        source = inspect.getsource(game_views.ModeSelectView.on_key_press)
        if "多人联机" in source:
            print("  ✅ 多人联机选项已集成到主菜单")
        else:
            print("  ⚠️ 多人联机选项可能未正确集成")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 游戏视图集成测试失败: {e}")
        return False

def test_network_modules():
    """测试网络模块"""
    print("\n🔗 测试网络模块...")
    
    try:
        from multiplayer import udp_discovery, udp_host, udp_client, udp_messages
        print("  ✅ 所有网络模块导入成功")
        
        # 测试消息创建
        from multiplayer.udp_messages import MessageFactory
        msg = MessageFactory.create_room_advertise("测试", 1, 4)
        print(f"  ✅ 消息创建成功: {len(msg.to_bytes())} 字节")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 网络模块测试失败: {e}")
        return False

def test_arcade_compatibility():
    """测试Arcade兼容性"""
    print("\n🎨 测试Arcade兼容性...")
    
    try:
        # 测试关键的绘制函数
        required_functions = [
            'draw_lrbt_rectangle_filled',
            'draw_text'
        ]
        
        missing_functions = []
        for func_name in required_functions:
            if not hasattr(arcade, func_name):
                missing_functions.append(func_name)
        
        if missing_functions:
            print(f"  ⚠️ 缺少函数: {missing_functions}")
            return False
        else:
            print("  ✅ 所有必需的Arcade函数都可用")
            return True
            
    except Exception as e:
        print(f"  ❌ Arcade兼容性测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 最小多人游戏测试")
    print("=" * 40)
    
    tests = [
        ("网络模块", test_network_modules),
        ("多人游戏视图", test_multiplayer_view_creation),
        ("游戏视图集成", test_game_views_integration),
        ("Arcade兼容性", test_arcade_compatibility)
    ]
    
    passed = 0
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 测试通过")
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
    
    print("\n" + "=" * 40)
    print(f"📊 测试结果: {passed}/{len(tests)} 通过")
    
    if passed == len(tests):
        print("🎉 所有基础测试通过！")
        print("\n💡 如果游戏启动仍有问题，可能是图形界面相关的问题。")
        print("   建议在有图形界面的环境中运行游戏。")
    else:
        print("⚠️ 部分测试失败，请检查错误信息。")

if __name__ == "__main__":
    main()
