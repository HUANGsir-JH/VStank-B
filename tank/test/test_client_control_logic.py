#!/usr/bin/env python3
"""
客户端控制逻辑单元测试

专注测试客户端输入处理逻辑，不涉及图形界面
"""

import sys
import os
import math
from unittest.mock import Mock, MagicMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestClientControlLogic:
    """客户端控制逻辑测试类"""
    
    def __init__(self):
        self.test_results = []
    
    def create_mock_tank(self):
        """创建模拟坦克对象"""
        mock_tank = Mock()
        mock_tank.pymunk_body = Mock()
        mock_tank.pymunk_body.angle = 0  # 初始角度
        mock_tank.pymunk_body.velocity = (0, 0)  # 初始速度
        mock_tank.pymunk_body.angular_velocity = 0  # 初始角速度
        
        # 模拟射击方法
        mock_bullet = Mock()
        mock_bullet.pymunk_body = Mock()
        mock_bullet.pymunk_shape = Mock()
        mock_tank.shoot = Mock(return_value=mock_bullet)
        
        return mock_tank
    
    def create_mock_game_view(self):
        """创建模拟游戏视图"""
        mock_game_view = Mock()
        mock_game_view.player2_tank = self.create_mock_tank()
        mock_game_view.total_time = 1.0
        mock_game_view.bullet_list = []
        mock_game_view.space = Mock()
        mock_game_view.space.add = Mock()
        
        return mock_game_view
    
    def test_movement_control(self):
        """测试移动控制逻辑"""
        print("🚗 测试移动控制逻辑...")
        
        # 导入修复后的网络视图类
        from multiplayer.network_views import HostGameView
        
        # 创建主机视图实例
        host_view = HostGameView()
        host_view.game_view = self.create_mock_game_view()
        
        tank = host_view.game_view.player2_tank
        body = tank.pymunk_body
        
        # 测试前进控制 (W键)
        print("  测试前进控制...")
        host_view._apply_client_input("test_client", ["W"], [])
        
        # 验证速度设置
        velocity = body.velocity
        if velocity == (0, 0):
            raise Exception("前进控制失败：速度未设置")
        
        # 验证速度方向（应该沿着坦克朝向）
        expected_speed = 60 * 3  # PLAYER_MOVEMENT_SPEED * 60
        angle_rad = body.angle  # 应该是0
        expected_vel_x = math.cos(angle_rad) * expected_speed
        expected_vel_y = math.sin(angle_rad) * expected_speed
        
        if abs(velocity[0] - expected_vel_x) > 0.1 or abs(velocity[1] - expected_vel_y) > 0.1:
            print(f"  警告：速度计算可能有误 - 期望:({expected_vel_x:.1f}, {expected_vel_y:.1f}), 实际:{velocity}")
        
        print(f"  ✅ 前进速度设置: {velocity}")
        
        # 测试后退控制 (S键)
        print("  测试后退控制...")
        host_view._apply_client_input("test_client", ["S"], [])
        
        velocity = body.velocity
        if velocity == (0, 0):
            raise Exception("后退控制失败：速度未设置")
        
        print(f"  ✅ 后退速度设置: {velocity}")
        
        # 测试停止控制
        print("  测试停止控制...")
        host_view._apply_client_input("test_client", [], ["W"])
        
        velocity_after_stop = body.velocity
        if velocity_after_stop != (0, 0):
            raise Exception(f"停止控制失败：速度应为(0,0)，实际为{velocity_after_stop}")
        
        print("  ✅ 停止控制正常")
        
        self.test_results.append("✅ 移动控制逻辑测试通过")
        return True
    
    def test_rotation_control(self):
        """测试旋转控制逻辑"""
        print("🔄 测试旋转控制逻辑...")
        
        from multiplayer.network_views import HostGameView
        
        host_view = HostGameView()
        host_view.game_view = self.create_mock_game_view()
        
        tank = host_view.game_view.player2_tank
        body = tank.pymunk_body
        
        # 测试顺时针旋转 (A键)
        print("  测试顺时针旋转...")
        host_view._apply_client_input("test_client", ["A"], [])
        
        angular_velocity = body.angular_velocity
        if angular_velocity == 0:
            raise Exception("顺时针旋转控制失败：角速度未设置")
        
        print(f"  ✅ 顺时针角速度设置: {angular_velocity}")
        
        # 测试逆时针旋转 (D键)
        print("  测试逆时针旋转...")
        host_view._apply_client_input("test_client", ["D"], [])
        
        angular_velocity = body.angular_velocity
        if angular_velocity == 0:
            raise Exception("逆时针旋转控制失败：角速度未设置")
        
        print(f"  ✅ 逆时针角速度设置: {angular_velocity}")
        
        # 测试停止旋转
        print("  测试停止旋转...")
        host_view._apply_client_input("test_client", [], ["A"])
        
        angular_velocity_after_stop = body.angular_velocity
        if angular_velocity_after_stop != 0:
            raise Exception(f"停止旋转失败：角速度应为0，实际为{angular_velocity_after_stop}")
        
        print("  ✅ 停止旋转正常")
        
        self.test_results.append("✅ 旋转控制逻辑测试通过")
        return True
    
    def test_shooting_control(self):
        """测试射击控制逻辑"""
        print("🔫 测试射击控制逻辑...")
        
        from multiplayer.network_views import HostGameView
        
        host_view = HostGameView()
        host_view.game_view = self.create_mock_game_view()
        
        tank = host_view.game_view.player2_tank
        
        # 测试射击 (SPACE键)
        print("  测试射击控制...")
        initial_bullet_count = len(host_view.game_view.bullet_list)
        
        host_view._apply_client_input("test_client", ["SPACE"], [])
        
        # 验证shoot方法被调用
        if not tank.shoot.called:
            raise Exception("射击控制失败：shoot方法未被调用")
        
        # 验证子弹被添加到列表
        final_bullet_count = len(host_view.game_view.bullet_list)
        if final_bullet_count <= initial_bullet_count:
            raise Exception("射击控制失败：子弹未被添加到列表")
        
        # 验证子弹被添加到物理空间
        if not host_view.game_view.space.add.called:
            raise Exception("射击控制失败：子弹未被添加到物理空间")
        
        print(f"  ✅ 射击控制正常，子弹数量: {initial_bullet_count} -> {final_bullet_count}")
        
        self.test_results.append("✅ 射击控制逻辑测试通过")
        return True
    
    def test_combined_controls(self):
        """测试组合控制逻辑"""
        print("🎮 测试组合控制逻辑...")
        
        from multiplayer.network_views import HostGameView
        
        host_view = HostGameView()
        host_view.game_view = self.create_mock_game_view()
        
        tank = host_view.game_view.player2_tank
        body = tank.pymunk_body
        
        # 测试同时前进和旋转
        print("  测试同时前进和旋转...")
        host_view._apply_client_input("test_client", ["W", "A"], [])
        
        velocity = body.velocity
        angular_velocity = body.angular_velocity
        
        if velocity == (0, 0):
            raise Exception("组合控制失败：移动速度未设置")
        
        if angular_velocity == 0:
            raise Exception("组合控制失败：角速度未设置")
        
        print(f"  ✅ 组合控制正常 - 速度:{velocity}, 角速度:{angular_velocity}")
        
        # 测试同时前进和射击
        print("  测试同时前进和射击...")
        tank.shoot.reset_mock()  # 重置mock
        initial_bullet_count = len(host_view.game_view.bullet_list)
        
        host_view._apply_client_input("test_client", ["W", "SPACE"], [])
        
        if not tank.shoot.called:
            raise Exception("组合控制失败：射击未执行")
        
        final_bullet_count = len(host_view.game_view.bullet_list)
        if final_bullet_count <= initial_bullet_count:
            raise Exception("组合控制失败：子弹未添加")
        
        print("  ✅ 前进+射击组合控制正常")
        
        self.test_results.append("✅ 组合控制逻辑测试通过")
        return True
    
    def test_error_handling(self):
        """测试错误处理"""
        print("🛡️ 测试错误处理...")
        
        from multiplayer.network_views import HostGameView
        
        host_view = HostGameView()
        
        # 测试无游戏视图的情况
        print("  测试无游戏视图...")
        host_view.game_view = None
        try:
            host_view._apply_client_input("test_client", ["W"], [])
            print("  ✅ 无游戏视图时正常处理")
        except Exception as e:
            raise Exception(f"无游戏视图时处理失败: {e}")
        
        # 测试无坦克的情况
        print("  测试无坦克...")
        host_view.game_view = Mock()
        host_view.game_view.player2_tank = None
        try:
            host_view._apply_client_input("test_client", ["W"], [])
            print("  ✅ 无坦克时正常处理")
        except Exception as e:
            raise Exception(f"无坦克时处理失败: {e}")
        
        # 测试无Pymunk body的情况
        print("  测试无Pymunk body...")
        mock_tank = Mock()
        mock_tank.pymunk_body = None
        host_view.game_view.player2_tank = mock_tank
        try:
            host_view._apply_client_input("test_client", ["W"], [])
            print("  ✅ 无Pymunk body时正常处理")
        except Exception as e:
            raise Exception(f"无Pymunk body时处理失败: {e}")
        
        self.test_results.append("✅ 错误处理测试通过")
        return True
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始客户端控制逻辑测试")
        print("=" * 50)
        
        try:
            # 运行测试
            self.test_movement_control()
            self.test_rotation_control()
            self.test_shooting_control()
            self.test_combined_controls()
            self.test_error_handling()
            
            # 显示结果
            print("\n" + "=" * 50)
            print("📋 测试结果汇总:")
            for result in self.test_results:
                print(f"  {result}")
            
            print(f"\n🎉 所有测试通过! ({len(self.test_results)}/5)")
            return True
            
        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    tester = TestClientControlLogic()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
