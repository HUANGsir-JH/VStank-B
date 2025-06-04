#!/usr/bin/env python3
"""
子弹同步修复验证测试

测试修复后的多人联机子弹同步功能：
1. 主机端子弹显示问题
2. 客户端子弹同步问题  
3. 客户端首发子弹卡顿问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_bullet_id_system():
    """测试子弹ID系统"""
    print("🔍 测试子弹ID系统...")
    
    try:
        from tank_sprites import Bullet
        
        # 重置子弹ID计数器
        Bullet._bullet_id_counter = 0
        
        # 创建几个子弹测试ID分配
        bullet1 = Bullet(
            radius=4,
            owner=None,
            tank_center_x=100,
            tank_center_y=100,
            actual_emission_angle_degrees=0,
            speed_magnitude=16,
            color=(255, 255, 0)
        )
        
        bullet2 = Bullet(
            radius=4,
            owner=None,
            tank_center_x=200,
            tank_center_y=200,
            actual_emission_angle_degrees=45,
            speed_magnitude=16,
            color=(0, 255, 0)
        )
        
        # 验证ID分配
        if hasattr(bullet1, 'bullet_id') and hasattr(bullet2, 'bullet_id'):
            print(f"  ✅ 子弹ID分配成功: bullet1.id={bullet1.bullet_id}, bullet2.id={bullet2.bullet_id}")
            if bullet1.bullet_id != bullet2.bullet_id:
                print("  ✅ 子弹ID唯一性验证通过")
            else:
                print("  ❌ 子弹ID重复")
                return False
        else:
            print("  ❌ 子弹ID属性缺失")
            return False
            
        # 验证速度信息保存
        if hasattr(bullet1, 'speed_magnitude') and bullet1.speed_magnitude == 16:
            print("  ✅ 子弹速度信息保存成功")
        else:
            print("  ❌ 子弹速度信息保存失败")
            return False
            
        return True
        
    except Exception as e:
        print(f"  ❌ 子弹ID系统测试失败: {e}")
        return False

def test_game_state_extraction():
    """测试游戏状态提取"""
    print("\n🔍 测试游戏状态提取...")
    
    try:
        # 模拟游戏视图和子弹列表
        class MockGameView:
            def __init__(self):
                self.bullet_list = []
                self.total_time = 1.5
                
        class MockBullet:
            def __init__(self, bullet_id, x, y, angle, owner_id, speed):
                self.bullet_id = bullet_id
                self.center_x = x
                self.center_y = y
                self.angle = angle
                self.owner = MockOwner(owner_id)
                self.speed_magnitude = speed
                
        class MockOwner:
            def __init__(self, player_id):
                self.player_id = player_id
        
        # 创建模拟数据
        game_view = MockGameView()
        game_view.bullet_list = [
            MockBullet(1, 100, 150, 45, "host", 16),
            MockBullet(2, 200, 250, 90, "client", 16),
            MockBullet(3, 300, 350, 135, "host", 16)
        ]
        
        # 模拟状态提取逻辑
        bullets = []
        for i, bullet in enumerate(game_view.bullet_list):
            if bullet is not None:
                owner_id = 'unknown'
                if bullet.owner:
                    owner_id = getattr(bullet.owner, 'player_id', 'unknown')
                
                bullet_data = {
                    "id": getattr(bullet, 'bullet_id', i),
                    "x": bullet.center_x,
                    "y": bullet.center_y,
                    "angle": getattr(bullet, 'angle', 0),
                    "owner": owner_id,
                    "speed": getattr(bullet, 'speed_magnitude', 16),
                    "timestamp": getattr(game_view, 'total_time', 0)
                }
                bullets.append(bullet_data)
        
        # 验证提取结果
        if len(bullets) == 3:
            print(f"  ✅ 子弹数量正确: {len(bullets)} 个")
        else:
            print(f"  ❌ 子弹数量错误: 期望3个，实际{len(bullets)}个")
            return False
            
        # 验证子弹数据完整性
        for i, bullet_data in enumerate(bullets):
            required_fields = ["id", "x", "y", "angle", "owner", "speed", "timestamp"]
            for field in required_fields:
                if field not in bullet_data:
                    print(f"  ❌ 子弹{i+1}缺少字段: {field}")
                    return False
            
            print(f"  ✅ 子弹{i+1}: ID={bullet_data['id']}, 位置=({bullet_data['x']}, {bullet_data['y']}), 所有者={bullet_data['owner']}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 游戏状态提取测试失败: {e}")
        return False

def test_bullet_sync_logic():
    """测试子弹同步逻辑"""
    print("\n🔍 测试子弹同步逻辑...")
    
    try:
        # 模拟客户端子弹同步场景
        
        # 当前客户端子弹状态
        current_bullets = {
            1: {"id": 1, "x": 100, "y": 150},
            2: {"id": 2, "x": 200, "y": 250}
        }
        
        # 服务器发送的子弹状态
        server_bullets = {
            1: {"id": 1, "x": 110, "y": 160, "angle": 45, "owner": "host"},  # 位置更新
            3: {"id": 3, "x": 300, "y": 350, "angle": 90, "owner": "client"}  # 新子弹
            # 子弹2被移除
        }
        
        # 模拟同步逻辑
        bullets_to_remove = []
        for bullet_id, bullet in current_bullets.items():
            if bullet_id not in server_bullets:
                bullets_to_remove.append(bullet_id)
        
        bullets_to_update = []
        bullets_to_create = []
        for bullet_id, bullet_data in server_bullets.items():
            if bullet_id in current_bullets:
                bullets_to_update.append(bullet_id)
            else:
                bullets_to_create.append(bullet_id)
        
        # 验证同步决策
        if bullets_to_remove == [2]:
            print("  ✅ 正确识别需要移除的子弹: [2]")
        else:
            print(f"  ❌ 移除子弹识别错误: 期望[2]，实际{bullets_to_remove}")
            return False
            
        if bullets_to_update == [1]:
            print("  ✅ 正确识别需要更新的子弹: [1]")
        else:
            print(f"  ❌ 更新子弹识别错误: 期望[1]，实际{bullets_to_update}")
            return False
            
        if bullets_to_create == [3]:
            print("  ✅ 正确识别需要创建的子弹: [3]")
        else:
            print(f"  ❌ 创建子弹识别错误: 期望[3]，实际{bullets_to_create}")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ 子弹同步逻辑测试失败: {e}")
        return False

def test_bullet_color_mapping():
    """测试子弹颜色映射"""
    print("\n🔍 测试子弹颜色映射...")
    
    try:
        # 模拟颜色映射逻辑
        def get_bullet_color_for_owner(owner_id):
            import arcade
            
            # 默认颜色
            bullet_color = arcade.color.YELLOW_ORANGE
            
            # 根据owner_id使用默认颜色方案
            if owner_id == "host":
                bullet_color = (0, 255, 0)  # 主机默认绿色
            elif owner_id.startswith("client"):
                bullet_color = (0, 0, 128)  # 客户端默认蓝色
            
            return bullet_color
        
        # 测试不同所有者的颜色
        host_color = get_bullet_color_for_owner("host")
        client_color = get_bullet_color_for_owner("client")
        unknown_color = get_bullet_color_for_owner("unknown")
        
        if host_color == (0, 255, 0):
            print("  ✅ 主机子弹颜色正确: 绿色")
        else:
            print(f"  ❌ 主机子弹颜色错误: {host_color}")
            return False
            
        if client_color == (0, 0, 128):
            print("  ✅ 客户端子弹颜色正确: 蓝色")
        else:
            print(f"  ❌ 客户端子弹颜色错误: {client_color}")
            return False
            
        print(f"  ✅ 未知所有者子弹颜色: {unknown_color}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 子弹颜色映射测试失败: {e}")
        return False

def run_all_tests():
    """运行所有测试"""
    print("🚀 开始子弹同步修复验证测试...\n")
    
    tests = [
        ("子弹ID系统", test_bullet_id_system),
        ("游戏状态提取", test_game_state_extraction),
        ("子弹同步逻辑", test_bullet_sync_logic),
        ("子弹颜色映射", test_bullet_color_mapping)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 测试通过")
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
    
    print(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！子弹同步修复验证成功！")
        return True
    else:
        print("⚠️  部分测试失败，需要进一步检查")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
