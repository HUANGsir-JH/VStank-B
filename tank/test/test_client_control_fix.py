#!/usr/bin/env python3
"""
客户端控制问题修复测试

测试客户端坦克的键盘输入处理、移动操作和子弹发射功能
"""

import sys
import os
import time
import threading
import socket
from unittest.mock import Mock, patch

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multiplayer.game_host import GameHost
from multiplayer.game_client import GameClient
from multiplayer.network_views import HostGameView
from multiplayer.messages import MessageFactory, MessageType
import game_views


class TestClientControlFix:
    """客户端控制修复测试类"""
    
    def __init__(self):
        self.host = None
        self.client = None
        self.host_view = None
        self.test_results = []
        
    def find_available_ports(self, count=2):
        """查找可用端口"""
        ports = []
        for port in range(12340, 12400):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.bind(('', port))
                sock.close()
                ports.append(port)
                if len(ports) >= count:
                    break
            except OSError:
                continue
        return ports
    
    def setup_host_client(self):
        """设置主机和客户端"""
        print("🔧 设置主机和客户端...")
        
        ports = self.find_available_ports(2)
        if len(ports) < 2:
            raise Exception("无法找到足够的可用端口")
        
        host_port = ports[0]
        
        # 创建主机
        self.host = GameHost(host_port)
        
        # 创建客户端
        self.client = GameClient()
        
        # 创建主机视图（模拟）
        self.host_view = Mock(spec=HostGameView)
        self.host_view.game_view = Mock(spec=game_views.GameView)
        
        # 模拟坦克对象
        mock_tank = Mock()
        mock_tank.pymunk_body = Mock()
        mock_tank.pymunk_body.angle = 0
        mock_tank.pymunk_body.velocity = (0, 0)
        mock_tank.pymunk_body.angular_velocity = 0
        mock_tank.shoot = Mock(return_value=None)
        
        self.host_view.game_view.player2_tank = mock_tank
        self.host_view.game_view.total_time = 0.0
        self.host_view.game_view.bullet_list = []
        self.host_view.game_view.space = Mock()
        
        return host_port
    
    def test_host_client_connection(self):
        """测试主机客户端连接"""
        print("\n🔗 测试主机客户端连接...")
        
        host_port = self.setup_host_client()
        
        # 设置回调
        connection_success = threading.Event()
        
        def on_client_join(client_id, player_name):
            print(f"✅ 客户端连接成功: {client_id} ({player_name})")
            connection_success.set()
        
        self.host.set_callbacks(client_join=on_client_join)
        
        # 启动主机
        if not self.host.start_hosting("测试房间", "测试主机"):
            raise Exception("主机启动失败")
        
        # 连接客户端
        if not self.client.connect_to_host("127.0.0.1", host_port, "测试客户端"):
            raise Exception("客户端连接失败")
        
        # 等待连接成功
        if not connection_success.wait(timeout=3.0):
            raise Exception("连接超时")
        
        self.test_results.append("✅ 主机客户端连接测试通过")
        return True
    
    def test_client_input_processing(self):
        """测试客户端输入处理"""
        print("\n🎮 测试客户端输入处理...")
        
        # 模拟输入接收
        input_received = threading.Event()
        received_inputs = []
        
        def on_input_received(client_id, keys_pressed, keys_released):
            received_inputs.append((client_id, keys_pressed, keys_released))
            print(f"📥 收到输入: {client_id} - 按下:{keys_pressed}, 释放:{keys_released}")
            input_received.set()
        
        self.host.set_callbacks(input_received=on_input_received)
        
        # 发送测试输入
        test_keys = ["W", "A", "SPACE"]
        for key in test_keys:
            self.client.send_key_press(key)
        
        # 等待输入接收
        if not input_received.wait(timeout=2.0):
            raise Exception("输入接收超时")
        
        # 验证输入
        if not received_inputs:
            raise Exception("未收到任何输入")
        
        last_input = received_inputs[-1]
        if not any(key in last_input[1] for key in test_keys):
            raise Exception(f"输入验证失败: 期望包含 {test_keys}, 实际收到 {last_input[1]}")
        
        self.test_results.append("✅ 客户端输入处理测试通过")
        return True
    
    def test_tank_control_logic(self):
        """测试坦克控制逻辑"""
        print("\n🚗 测试坦克控制逻辑...")
        
        # 导入修复后的网络视图
        from multiplayer.network_views import HostGameView
        
        # 创建真实的主机视图实例
        real_host_view = HostGameView()
        real_host_view.game_view = self.host_view.game_view
        
        # 测试移动控制
        print("  测试前进控制...")
        real_host_view._apply_client_input("test_client", ["W"], [])
        
        # 验证速度设置
        tank = self.host_view.game_view.player2_tank
        velocity = tank.pymunk_body.velocity
        if velocity == (0, 0):
            raise Exception("前进控制失败：速度未设置")
        
        print(f"  ✅ 前进速度设置: {velocity}")
        
        # 测试停止控制
        print("  测试停止控制...")
        real_host_view._apply_client_input("test_client", [], ["W"])
        
        velocity_after_stop = tank.pymunk_body.velocity
        if velocity_after_stop != (0, 0):
            raise Exception(f"停止控制失败：速度应为(0,0)，实际为{velocity_after_stop}")
        
        print("  ✅ 停止控制正常")
        
        # 测试旋转控制
        print("  测试旋转控制...")
        real_host_view._apply_client_input("test_client", ["A"], [])
        
        angular_velocity = tank.pymunk_body.angular_velocity
        if angular_velocity == 0:
            raise Exception("旋转控制失败：角速度未设置")
        
        print(f"  ✅ 旋转速度设置: {angular_velocity}")
        
        # 测试射击控制
        print("  测试射击控制...")
        tank.shoot.reset_mock()  # 重置mock
        real_host_view._apply_client_input("test_client", ["SPACE"], [])
        
        if not tank.shoot.called:
            raise Exception("射击控制失败：shoot方法未被调用")
        
        print("  ✅ 射击控制正常")
        
        self.test_results.append("✅ 坦克控制逻辑测试通过")
        return True
    
    def test_network_sync(self):
        """测试网络同步"""
        print("\n🌐 测试网络同步...")
        
        # 模拟游戏状态同步
        sync_received = threading.Event()
        
        def on_game_state(state):
            print(f"📊 收到游戏状态: {len(state.get('tanks', []))} 个坦克")
            sync_received.set()
        
        self.client.set_callbacks(game_state=on_game_state)
        
        # 主机发送游戏状态
        game_state = {
            "tanks": [
                {"x": 100, "y": 100, "angle": 0, "health": 100, "player_id": "host"},
                {"x": 200, "y": 200, "angle": 90, "health": 100, "player_id": "client"}
            ],
            "bullets": [],
            "scores": {"host": 0, "client": 0}
        }
        
        self.host.send_game_state(game_state)
        
        # 等待同步
        if not sync_received.wait(timeout=2.0):
            raise Exception("游戏状态同步超时")
        
        self.test_results.append("✅ 网络同步测试通过")
        return True
    
    def cleanup(self):
        """清理资源"""
        print("\n🧹 清理测试资源...")
        
        if self.client:
            self.client.disconnect()
        
        if self.host:
            self.host.stop_hosting()
        
        time.sleep(0.5)  # 等待清理完成
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始客户端控制修复测试")
        print("=" * 50)
        
        try:
            # 运行测试
            self.test_host_client_connection()
            self.test_client_input_processing()
            self.test_tank_control_logic()
            self.test_network_sync()
            
            # 显示结果
            print("\n" + "=" * 50)
            print("📋 测试结果汇总:")
            for result in self.test_results:
                print(f"  {result}")
            
            print(f"\n🎉 所有测试通过! ({len(self.test_results)}/4)")
            return True
            
        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            return False
        
        finally:
            self.cleanup()


if __name__ == "__main__":
    tester = TestClientControlFix()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
