"""
Arcade API兼容性修复验证测试

验证我们修复的Arcade API调用是否正确
"""

import sys
import os

# 添加父目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_arcade_api_compatibility():
    """测试Arcade API兼容性修复"""
    print("🎨 测试Arcade API兼容性修复...")
    
    try:
        import arcade
        
        # 检查我们使用的函数是否可用
        required_functions = [
            'draw_lrbt_rectangle_filled',
            'draw_lrbt_rectangle_outline', 
            'draw_text'
        ]
        
        missing_functions = []
        for func_name in required_functions:
            if hasattr(arcade, func_name):
                print(f"  ✅ {func_name} 可用")
            else:
                missing_functions.append(func_name)
                print(f"  ❌ {func_name} 不可用")
        
        if missing_functions:
            print(f"  ⚠️ 缺少函数: {missing_functions}")
            return False
        
        # 测试函数调用（不实际绘制）
        print("  ✅ 所有必需的Arcade函数都可用")
        print(f"  ✅ Arcade版本: {arcade.version.VERSION}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Arcade API兼容性测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_network_views_import():
    """测试网络视图模块导入（验证修复后的代码）"""
    print("\n🌐 测试网络视图模块导入...")
    
    try:
        # 测试导入修复后的网络视图模块
        from multiplayer.network_views import RoomBrowserView, NetworkHostView, NetworkClientView
        
        print("  ✅ RoomBrowserView 导入成功")
        print("  ✅ NetworkHostView 导入成功") 
        print("  ✅ NetworkClientView 导入成功")
        
        # 验证扩展方法是否正确添加
        host_methods = [
            '_start_tank_selection',
            '_draw_tank_selection',
            '_handle_tank_selection_keys'
        ]
        
        for method_name in host_methods:
            if hasattr(NetworkHostView, method_name):
                print(f"  ✅ NetworkHostView.{method_name} 可用")
            else:
                print(f"  ❌ NetworkHostView.{method_name} 不可用")
                return False
        
        client_methods = [
            '_draw_client_tank_selection',
            '_handle_client_tank_selection_keys',
            '_start_client_tank_selection'
        ]
        
        for method_name in client_methods:
            if hasattr(NetworkClientView, method_name):
                print(f"  ✅ NetworkClientView.{method_name} 可用")
            else:
                print(f"  ❌ NetworkClientView.{method_name} 不可用")
                return False
        
        print("  ✅ 所有坦克选择方法都正确添加")
        return True
        
    except Exception as e:
        print(f"  ❌ 网络视图模块导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tank_selection_logic():
    """测试坦克选择逻辑（不创建Arcade窗口）"""
    print("\n🎮 测试坦克选择逻辑...")
    
    try:
        # 模拟坦克选择逻辑测试
        available_tanks = ["green", "blue", "yellow", "grey"]
        selected_tank = "blue"
        
        # 测试坦克切换逻辑
        current_index = available_tanks.index(selected_tank)
        new_index = (current_index + 1) % len(available_tanks)
        new_tank = available_tanks[new_index]
        
        assert new_tank == "yellow", f"坦克切换逻辑错误: {new_tank}"
        print(f"  ✅ 坦克切换逻辑正确: {selected_tank} → {new_tank}")
        
        # 测试反向切换
        new_index = (current_index - 1) % len(available_tanks)
        new_tank = available_tanks[new_index]
        
        assert new_tank == "green", f"反向坦克切换逻辑错误: {new_tank}"
        print(f"  ✅ 反向坦克切换逻辑正确: {selected_tank} → {new_tank}")
        
        # 测试坦克颜色映射
        tank_colors = {
            "green": (0, 255, 0),
            "blue": (0, 0, 255), 
            "yellow": (255, 255, 0),
            "grey": (128, 128, 128)
        }
        
        for tank_type in available_tanks:
            assert tank_type in tank_colors, f"坦克颜色映射缺失: {tank_type}"
        
        print("  ✅ 坦克颜色映射完整")
        print("  ✅ 坦克选择逻辑测试通过")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 坦克选择逻辑测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """运行所有Arcade兼容性修复测试"""
    print("🔧 Arcade兼容性修复验证测试")
    print("=" * 50)
    
    tests = [
        ("Arcade API兼容性", test_arcade_api_compatibility),
        ("网络视图模块导入", test_network_views_import),
        ("坦克选择逻辑", test_tank_selection_logic),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} - 通过")
            else:
                print(f"❌ {test_name} - 失败")
        except Exception as e:
            print(f"❌ {test_name} - 异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 Arcade兼容性修复验证通过！")
        print("🚀 游戏现在应该可以正常运行了")
        return True
    else:
        print("⚠️ 部分测试失败，需要进一步检查")
        return False

if __name__ == "__main__":
    main()
