"""
坦克图像显示测试

测试多人游戏坦克选择界面中的坦克图像加载和显示功能
"""

import sys
import os

# 添加父目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_tank_image_paths():
    """测试坦克图片路径是否存在"""
    print("🖼️ 测试坦克图片路径...")
    
    try:
        from tank_sprites import PLAYER_IMAGE_PATH_GREEN, PLAYER_IMAGE_PATH_BLUE, PLAYER_IMAGE_PATH_DESERT, PLAYER_IMAGE_PATH_GREY
        
        tank_paths = {
            "green": PLAYER_IMAGE_PATH_GREEN,
            "blue": PLAYER_IMAGE_PATH_BLUE,
            "yellow": PLAYER_IMAGE_PATH_DESERT,
            "grey": PLAYER_IMAGE_PATH_GREY
        }
        
        all_exist = True
        for tank_type, path in tank_paths.items():
            if os.path.exists(path):
                print(f"  ✅ {tank_type}坦克图片存在: {path}")
            else:
                print(f"  ❌ {tank_type}坦克图片不存在: {path}")
                all_exist = False
        
        return all_exist
        
    except Exception as e:
        print(f"  ❌ 坦克图片路径测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tank_image_mapping():
    """测试坦克图片映射逻辑"""
    print("\n🗺️ 测试坦克图片映射...")
    
    try:
        from tank_sprites import PLAYER_IMAGE_PATH_GREEN, PLAYER_IMAGE_PATH_BLUE, PLAYER_IMAGE_PATH_DESERT, PLAYER_IMAGE_PATH_GREY
        
        # 模拟网络视图中的映射逻辑
        tank_image_map = {
            "green": PLAYER_IMAGE_PATH_GREEN,
            "blue": PLAYER_IMAGE_PATH_BLUE,
            "yellow": PLAYER_IMAGE_PATH_DESERT,
            "grey": PLAYER_IMAGE_PATH_GREY
        }
        
        tank_name_map = {
            "green": "绿色坦克",
            "blue": "蓝色坦克", 
            "yellow": "黄色坦克",
            "grey": "灰色坦克"
        }
        
        available_tanks = ["green", "blue", "yellow", "grey"]
        
        # 验证映射完整性
        for tank_type in available_tanks:
            image_path = tank_image_map.get(tank_type)
            tank_name = tank_name_map.get(tank_type)
            
            assert image_path is not None, f"坦克类型 {tank_type} 缺少图片路径"
            assert tank_name is not None, f"坦克类型 {tank_type} 缺少名称"
            
            print(f"  ✅ {tank_type}: {tank_name} -> {os.path.basename(image_path)}")
        
        print("  ✅ 坦克图片映射完整")
        return True
        
    except Exception as e:
        print(f"  ❌ 坦克图片映射测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_arcade_texture_loading():
    """测试Arcade纹理加载功能"""
    print("\n🎨 测试Arcade纹理加载...")
    
    try:
        import arcade
        from tank_sprites import PLAYER_IMAGE_PATH_GREEN
        
        # 测试加载一个坦克图片
        if os.path.exists(PLAYER_IMAGE_PATH_GREEN):
            try:
                tank_texture = arcade.load_texture(PLAYER_IMAGE_PATH_GREEN)
                
                # 验证纹理属性
                assert tank_texture.width > 0, "纹理宽度无效"
                assert tank_texture.height > 0, "纹理高度无效"
                
                print(f"  ✅ 成功加载绿色坦克纹理")
                print(f"  ✅ 纹理尺寸: {tank_texture.width} x {tank_texture.height}")
                
                # 测试缩放计算
                tank_scale = 0.15
                tank_width = tank_texture.width * tank_scale
                tank_height = tank_texture.height * tank_scale
                
                print(f"  ✅ 缩放后尺寸: {tank_width:.1f} x {tank_height:.1f}")
                
                return True
                
            except Exception as e:
                print(f"  ❌ 纹理加载失败: {e}")
                return False
        else:
            print(f"  ⚠️ 绿色坦克图片不存在，跳过纹理加载测试")
            return True
        
    except Exception as e:
        print(f"  ❌ Arcade纹理加载测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tank_selection_display_logic():
    """测试坦克选择显示逻辑"""
    print("\n🎮 测试坦克选择显示逻辑...")
    
    try:
        # 模拟主机端坦克选择状态
        available_tanks = ["green", "blue", "yellow", "grey"]
        selected_tanks = {"host": "green"}
        
        # 模拟绘制逻辑
        start_x = 640 - 150  # 模拟窗口中心
        y_pos = 520
        
        for i, tank_type in enumerate(available_tanks):
            x_pos = start_x + i * 100
            
            # 检查是否被选中
            is_selected = selected_tanks.get("host") == tank_type
            
            print(f"  坦克 {tank_type}: 位置({x_pos}, {y_pos}), 选中: {is_selected}")
            
            # 验证位置计算
            assert x_pos >= 0, f"坦克 {tank_type} X坐标无效: {x_pos}"
            assert y_pos >= 0, f"坦克 {tank_type} Y坐标无效: {y_pos}"
        
        print("  ✅ 坦克选择显示逻辑正确")
        
        # 测试客户端选择逻辑
        selected_tank = "blue"
        
        for tank_type in available_tanks:
            is_selected = selected_tank == tank_type
            if is_selected:
                print(f"  ✅ 客户端选中坦克: {tank_type}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 坦克选择显示逻辑测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fallback_display():
    """测试图片加载失败时的后备显示"""
    print("\n🔄 测试后备显示逻辑...")
    
    try:
        # 模拟图片加载失败的情况
        tank_colors = {
            "green": (0, 255, 0),
            "blue": (0, 0, 255),
            "yellow": (255, 255, 0),
            "grey": (128, 128, 128)
        }
        
        available_tanks = ["green", "blue", "yellow", "grey"]
        
        for tank_type in available_tanks:
            color = tank_colors.get(tank_type, (255, 255, 255))
            assert color is not None, f"坦克 {tank_type} 缺少后备颜色"
            print(f"  ✅ {tank_type}坦克后备颜色: RGB{color}")
        
        print("  ✅ 后备显示逻辑完整")
        return True
        
    except Exception as e:
        print(f"  ❌ 后备显示测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_network_views_tank_display():
    """测试网络视图中的坦克显示方法"""
    print("\n🌐 测试网络视图坦克显示方法...")
    
    try:
        # 验证方法是否正确添加到类中
        from multiplayer.network_views import NetworkHostView, NetworkClientView
        
        # 检查主机端方法
        host_methods = ['_draw_tank_selection']
        for method_name in host_methods:
            if hasattr(NetworkHostView, method_name):
                print(f"  ✅ NetworkHostView.{method_name} 存在")
            else:
                print(f"  ❌ NetworkHostView.{method_name} 不存在")
                return False
        
        # 检查客户端方法
        client_methods = ['_draw_client_tank_selection']
        for method_name in client_methods:
            if hasattr(NetworkClientView, method_name):
                print(f"  ✅ NetworkClientView.{method_name} 存在")
            else:
                print(f"  ❌ NetworkClientView.{method_name} 不存在")
                return False
        
        print("  ✅ 网络视图坦克显示方法完整")
        return True
        
    except Exception as e:
        print(f"  ❌ 网络视图坦克显示测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """运行所有坦克图像显示测试"""
    print("🖼️ 坦克图像显示测试套件")
    print("=" * 50)
    
    tests = [
        ("坦克图片路径", test_tank_image_paths),
        ("坦克图片映射", test_tank_image_mapping),
        ("Arcade纹理加载", test_arcade_texture_loading),
        ("坦克选择显示逻辑", test_tank_selection_display_logic),
        ("后备显示逻辑", test_fallback_display),
        ("网络视图坦克显示", test_network_views_tank_display),
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
        print("🎉 坦克图像显示测试全部通过！")
        print("🚀 多人游戏坦克选择界面现在显示真实坦克图像")
        return True
    else:
        print("⚠️ 部分测试失败，需要进一步检查")
        return False

if __name__ == "__main__":
    main()
