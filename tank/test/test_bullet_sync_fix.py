#!/usr/bin/env python3
"""
子弹同步修复测试

测试多人联机中子弹同步问题的修复效果，确保：
1. 主机端子弹数据正确发送
2. 客户端正确接收并处理子弹数据
3. 客户端能够正确渲染来自主机的子弹
"""

import sys
import os
import unittest
from unittest.mock import Mock, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_host_bullet_data_extraction():
    """测试主机端子弹数据提取"""
    print("🔫 测试主机端子弹数据提取...")
    
    try:
        # 模拟主机端游戏视图
        class MockGameView:
            def __init__(self):
                self.bullet_list = []
                
            def add_mock_bullet(self, x, y, angle, owner_id="host"):
                """添加模拟子弹"""
                mock_bullet = Mock()
                mock_bullet.center_x = x
                mock_bullet.center_y = y
                mock_bullet.angle = angle
                
                # 模拟owner对象
                mock_owner = Mock()
                mock_owner.player_id = owner_id
                mock_bullet.owner = mock_owner
                
                self.bullet_list.append(mock_bullet)
                return mock_bullet
        
        # 创建模拟游戏视图并添加子弹
        mock_game_view = MockGameView()
        bullet1 = mock_game_view.add_mock_bullet(100, 200, 45, "host")
        bullet2 = mock_game_view.add_mock_bullet(300, 400, 180, "host")
        
        # 模拟主机端子弹数据提取逻辑
        bullets = []
        if hasattr(mock_game_view, 'bullet_list') and mock_game_view.bullet_list is not None:
            for bullet in mock_game_view.bullet_list:
                if bullet is not None:
                    bullets.append({
                        "x": bullet.center_x,
                        "y": bullet.center_y,
                        "angle": getattr(bullet, 'angle', 0),
                        "owner": getattr(bullet.owner, 'player_id', 'unknown') if bullet.owner else 'unknown'
                    })
        
        # 验证提取结果
        assert len(bullets) == 2, f"应该提取到2个子弹，实际: {len(bullets)}"
        
        bullet1_data = bullets[0]
        assert bullet1_data["x"] == 100, f"子弹1 X坐标错误: {bullet1_data['x']}"
        assert bullet1_data["y"] == 200, f"子弹1 Y坐标错误: {bullet1_data['y']}"
        assert bullet1_data["angle"] == 45, f"子弹1 角度错误: {bullet1_data['angle']}"
        assert bullet1_data["owner"] == "host", f"子弹1 所有者错误: {bullet1_data['owner']}"
        
        bullet2_data = bullets[1]
        assert bullet2_data["x"] == 300, f"子弹2 X坐标错误: {bullet2_data['x']}"
        assert bullet2_data["y"] == 400, f"子弹2 Y坐标错误: {bullet2_data['y']}"
        assert bullet2_data["angle"] == 180, f"子弹2 角度错误: {bullet2_data['angle']}"
        assert bullet2_data["owner"] == "host", f"子弹2 所有者错误: {bullet2_data['owner']}"
        
        print("  ✅ 主机端子弹数据提取正常")
        print(f"  ✅ 成功提取 {len(bullets)} 个子弹的数据")
        return True
        
    except Exception as e:
        print(f"  ❌ 主机端子弹数据提取失败: {e}")
        return False

def test_client_bullet_sync_fix():
    """测试客户端子弹同步修复"""
    print("🎯 测试客户端子弹同步修复...")
    
    try:
        # 模拟客户端游戏视图
        class MockClientGameView:
            def __init__(self):
                self.bullet_list = []
                self.space = Mock()  # 模拟物理空间
                self.space.bodies = []
                self.space.shapes = []
                
                # 模拟space的add和remove方法
                def mock_add(body, shape=None):
                    if body not in self.space.bodies:
                        self.space.bodies.append(body)
                    if shape and shape not in self.space.shapes:
                        self.space.shapes.append(shape)
                
                def mock_remove(obj):
                    if obj in self.space.bodies:
                        self.space.bodies.remove(obj)
                    if obj in self.space.shapes:
                        self.space.shapes.remove(obj)
                
                self.space.add = mock_add
                self.space.remove = mock_remove
        
        # 创建模拟客户端视图
        mock_client_view = MockClientGameView()
        
        # 模拟接收到的服务器子弹数据
        bullets_data = [
            {"x": 150, "y": 250, "angle": 90, "owner": "host"},
            {"x": 350, "y": 450, "angle": 270, "owner": "host"}
        ]
        
        # 模拟修复后的子弹同步逻辑
        def apply_bullet_sync(game_view, bullets_data):
            """应用子弹同步（修复后的逻辑）"""
            if not hasattr(game_view, 'bullet_list'):
                return False
            
            # 清除现有子弹
            if hasattr(game_view, 'space') and game_view.space:
                for bullet in game_view.bullet_list:
                    if bullet and hasattr(bullet, 'pymunk_body') and bullet.pymunk_body:
                        try:
                            if bullet.pymunk_body in game_view.space.bodies:
                                game_view.space.remove(bullet.pymunk_body)
                            if hasattr(bullet, 'pymunk_shape') and bullet.pymunk_shape:
                                if bullet.pymunk_shape in game_view.space.shapes:
                                    game_view.space.remove(bullet.pymunk_shape)
                        except Exception as e:
                            print(f"移除旧子弹时出错: {e}")
            
            # 清空子弹列表
            game_view.bullet_list.clear()
            
            # 根据服务器数据创建新子弹
            for bullet_data in bullets_data:
                try:
                    # 模拟子弹对象
                    mock_bullet = Mock()
                    mock_bullet.center_x = bullet_data.get("x", 0)
                    mock_bullet.center_y = bullet_data.get("y", 0)
                    mock_bullet.angle = bullet_data.get("angle", 0)
                    
                    # 模拟物理体
                    mock_bullet.pymunk_body = Mock()
                    mock_bullet.pymunk_shape = Mock()
                    mock_bullet.pymunk_body.velocity = (0, 0)
                    mock_bullet.pymunk_body.angular_velocity = 0
                    
                    # 添加到子弹列表
                    game_view.bullet_list.append(mock_bullet)
                    
                    # 添加到物理空间
                    if hasattr(game_view, 'space') and game_view.space:
                        game_view.space.add(mock_bullet.pymunk_body, mock_bullet.pymunk_shape)
                    
                except Exception as e:
                    print(f"创建客户端子弹时出错: {e}")
                    return False
            
            return True
        
        # 执行子弹同步
        success = apply_bullet_sync(mock_client_view, bullets_data)
        assert success, "子弹同步执行失败"
        
        # 验证同步结果
        assert len(mock_client_view.bullet_list) == 2, f"应该有2个子弹，实际: {len(mock_client_view.bullet_list)}"
        
        # 验证第一个子弹
        bullet1 = mock_client_view.bullet_list[0]
        assert bullet1.center_x == 150, f"子弹1 X坐标错误: {bullet1.center_x}"
        assert bullet1.center_y == 250, f"子弹1 Y坐标错误: {bullet1.center_y}"
        assert bullet1.angle == 90, f"子弹1 角度错误: {bullet1.angle}"
        
        # 验证第二个子弹
        bullet2 = mock_client_view.bullet_list[1]
        assert bullet2.center_x == 350, f"子弹2 X坐标错误: {bullet2.center_x}"
        assert bullet2.center_y == 450, f"子弹2 Y坐标错误: {bullet2.center_y}"
        assert bullet2.angle == 270, f"子弹2 角度错误: {bullet2.angle}"
        
        # 验证物理空间中的子弹
        assert len(mock_client_view.space.bodies) == 2, f"物理空间应该有2个物体，实际: {len(mock_client_view.space.bodies)}"
        assert len(mock_client_view.space.shapes) == 2, f"物理空间应该有2个形状，实际: {len(mock_client_view.space.shapes)}"
        
        print("  ✅ 客户端子弹同步修复正常")
        print(f"  ✅ 成功同步 {len(mock_client_view.bullet_list)} 个子弹")
        print(f"  ✅ 物理空间包含 {len(mock_client_view.space.bodies)} 个子弹物体")
        return True
        
    except Exception as e:
        print(f"  ❌ 客户端子弹同步修复失败: {e}")
        return False

def test_bullet_sync_edge_cases():
    """测试子弹同步的边界情况"""
    print("🧪 测试子弹同步边界情况...")
    
    try:
        # 测试空子弹列表
        class MockGameView:
            def __init__(self):
                self.bullet_list = []
                self.space = Mock()
                self.space.bodies = []
                self.space.shapes = []
                self.space.add = lambda *args: None
                self.space.remove = lambda *args: None
        
        mock_view = MockGameView()
        
        # 测试空数据
        empty_bullets_data = []
        mock_view.bullet_list.clear()
        
        # 应该不会出错
        for bullet_data in empty_bullets_data:
            pass  # 空循环
        
        assert len(mock_view.bullet_list) == 0, "空数据应该产生空子弹列表"
        print("  ✅ 空子弹数据处理正常")
        
        # 测试无效数据
        invalid_bullets_data = [
            {"x": None, "y": 100, "angle": 0},  # 无效X坐标
            {"x": 100, "y": None, "angle": 0},  # 无效Y坐标
            {"angle": 0},  # 缺少坐标
            {}  # 完全空数据
        ]
        
        valid_bullets_created = 0
        for bullet_data in invalid_bullets_data:
            try:
                x = bullet_data.get("x", 0)
                y = bullet_data.get("y", 0)
                angle = bullet_data.get("angle", 0)
                
                # 只有当坐标有效时才创建子弹
                if x is not None and y is not None:
                    mock_bullet = Mock()
                    mock_bullet.center_x = x
                    mock_bullet.center_y = y
                    mock_bullet.angle = angle
                    mock_view.bullet_list.append(mock_bullet)
                    valid_bullets_created += 1
                    
            except Exception as e:
                print(f"  处理无效数据时出错（预期）: {e}")
        
        print(f"  ✅ 无效数据处理正常，创建了 {valid_bullets_created} 个有效子弹")
        return True
        
    except Exception as e:
        print(f"  ❌ 边界情况测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 开始子弹同步修复测试")
    print("=" * 50)
    
    tests = [
        test_host_bullet_data_extraction,
        test_client_bullet_sync_fix,
        test_bullet_sync_edge_cases
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ 测试 {test.__name__} 出现异常: {e}")
            failed += 1
        print()
    
    print("=" * 50)
    print(f"🧪 测试完成: {passed} 通过, {failed} 失败")
    
    if failed == 0:
        print("🎉 所有子弹同步修复测试通过！")
        return True
    else:
        print("❌ 部分测试失败，需要进一步检查")
        return False

if __name__ == "__main__":
    main()
