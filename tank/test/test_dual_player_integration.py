"""
双人游戏集成测试

测试主机和客户端之间的完整交互流程
"""

import unittest
import time
import threading
import socket
from unittest.mock import Mock, patch
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from multiplayer.dual_player_host import DualPlayerHost
from multiplayer.dual_player_client import DualPlayerClient
from multiplayer.udp_messages import MessageFactory, MessageType


class TestDualPlayerIntegration(unittest.TestCase):
    """双人游戏集成测试"""

    def setUp(self):
        # 使用不同的端口避免冲突
        self.host_port = 12348
        self.host = DualPlayerHost(host_port=self.host_port)
        self.client = DualPlayerClient()
        
        # 测试回调记录
        self.host_callbacks = {
            'client_join': Mock(),
            'client_leave': Mock(),
            'input_received': Mock()
        }
        
        self.client_callbacks = {
            'connection': Mock(),
            'disconnection': Mock(),
            'game_state': Mock()
        }

    def tearDown(self):
        # 清理资源
        if self.client.connected:
            self.client.disconnect()
        if self.host.running:
            self.host.stop_hosting(force=True)
        time.sleep(0.1)  # 等待清理完成

    def test_dual_player_connection_flow(self):
        """测试双人游戏连接流程"""
        # 设置主机回调
        self.host.set_callbacks(
            client_join=self.host_callbacks['client_join'],
            client_leave=self.host_callbacks['client_leave'],
            input_received=self.host_callbacks['input_received']
        )
        
        # 设置客户端回调
        self.client.set_callbacks(
            connection=self.client_callbacks['connection'],
            disconnection=self.client_callbacks['disconnection'],
            game_state=self.client_callbacks['game_state']
        )
        
        # 启动主机
        success = self.host.start_hosting("TestRoom")
        self.assertTrue(success)
        self.assertTrue(self.host.running)
        
        # 等待主机完全启动
        time.sleep(0.2)
        
        # 客户端连接
        connection_success = self.client.connect_to_host("127.0.0.1", self.host_port, "TestPlayer")
        self.assertTrue(connection_success)
        self.assertTrue(self.client.connected)
        
        # 等待连接建立
        time.sleep(0.2)
        
        # 验证主机端状态
        self.assertEqual(self.host.get_current_player_count(), 2)
        self.assertTrue(self.host.is_room_full())
        self.assertIsNotNone(self.host.client)
        self.assertEqual(self.host.client.player_name, "TestPlayer")
        
        # 验证客户端状态
        self.assertIsNotNone(self.client.player_id)
        self.assertEqual(self.client.player_name, "TestPlayer")
        
        # 验证回调被调用
        self.host_callbacks['client_join'].assert_called_once()
        self.client_callbacks['connection'].assert_called_once()

    def test_dual_player_input_synchronization(self):
        """测试双人游戏输入同步"""
        # 建立连接
        self.host.start_hosting("TestRoom")
        time.sleep(0.1)
        
        self.host.set_callbacks(input_received=self.host_callbacks['input_received'])
        
        self.client.connect_to_host("127.0.0.1", self.host_port, "TestPlayer")
        time.sleep(0.2)
        
        # 客户端发送输入
        self.client.send_key_press("W")
        self.client.send_key_press("SPACE")
        
        # 等待输入传输
        time.sleep(0.2)
        
        # 验证主机收到输入
        self.host_callbacks['input_received'].assert_called()
        
        # 验证主机端输入状态
        client_input = self.host.get_client_input()
        self.assertIn("W", client_input)
        self.assertIn("SPACE", client_input)

    def test_dual_player_game_state_broadcast(self):
        """测试双人游戏状态广播"""
        # 建立连接
        self.host.start_hosting("TestRoom")
        time.sleep(0.1)
        
        self.client.set_callbacks(game_state=self.client_callbacks['game_state'])
        self.client.connect_to_host("127.0.0.1", self.host_port, "TestPlayer")
        time.sleep(0.2)
        
        # 主机发送游戏状态
        game_state = {
            "tanks": [
                {"id": "host", "x": 100, "y": 100, "angle": 0},
                {"id": self.host.get_client_id(), "x": 200, "y": 200, "angle": 90}
            ],
            "bullets": [{"x": 150, "y": 150, "angle": 45}],
            "round_info": {"score": [1, 0], "round": 1}
        }
        
        self.host.send_game_state(game_state)
        
        # 等待状态传输
        time.sleep(0.2)
        
        # 验证客户端收到游戏状态
        self.client_callbacks['game_state'].assert_called()

    def test_dual_player_disconnection_flow(self):
        """测试双人游戏断开连接流程"""
        # 建立连接
        self.host.start_hosting("TestRoom")
        time.sleep(0.1)
        
        self.host.set_callbacks(client_leave=self.host_callbacks['client_leave'])
        self.client.set_callbacks(disconnection=self.client_callbacks['disconnection'])
        
        self.client.connect_to_host("127.0.0.1", self.host_port, "TestPlayer")
        time.sleep(0.2)
        
        # 验证连接建立
        self.assertEqual(self.host.get_current_player_count(), 2)
        self.assertTrue(self.client.connected)
        
        # 客户端主动断开连接
        self.client.disconnect()
        time.sleep(0.2)
        
        # 验证断开连接状态
        self.assertFalse(self.client.connected)
        self.assertEqual(self.host.get_current_player_count(), 1)
        self.assertIsNone(self.host.client)
        
        # 验证回调被调用
        self.client_callbacks['disconnection'].assert_called()

    def test_dual_player_room_full_rejection(self):
        """测试双人游戏房间满员拒绝"""
        # 启动主机
        self.host.start_hosting("TestRoom")
        time.sleep(0.1)
        
        # 第一个客户端连接成功
        client1 = DualPlayerClient()
        success1 = client1.connect_to_host("127.0.0.1", self.host_port, "Player1")
        self.assertTrue(success1)
        time.sleep(0.2)
        
        # 验证房间已满
        self.assertTrue(self.host.is_room_full())
        
        # 第二个客户端尝试连接应该被拒绝
        client2 = DualPlayerClient()
        success2 = client2.connect_to_host("127.0.0.1", self.host_port, "Player2")
        self.assertFalse(success2)
        
        # 验证只有一个客户端连接
        self.assertEqual(self.host.get_current_player_count(), 2)
        
        # 清理
        client1.disconnect()
        if client2.connected:
            client2.disconnect()

    def test_dual_player_heartbeat_mechanism(self):
        """测试双人游戏心跳机制"""
        # 建立连接
        self.host.start_hosting("TestRoom")
        time.sleep(0.1)
        
        self.client.connect_to_host("127.0.0.1", self.host_port, "TestPlayer")
        time.sleep(0.2)
        
        # 获取初始心跳时间
        initial_heartbeat = self.host.client.last_heartbeat
        
        # 等待心跳更新
        time.sleep(1.5)  # 等待超过心跳间隔
        
        # 验证心跳被更新
        self.assertGreater(self.host.client.last_heartbeat, initial_heartbeat)

    def test_dual_player_timeout_handling(self):
        """测试双人游戏超时处理"""
        # 建立连接
        self.host.start_hosting("TestRoom")
        time.sleep(0.1)
        
        self.host.set_callbacks(client_leave=self.host_callbacks['client_leave'])
        
        self.client.connect_to_host("127.0.0.1", self.host_port, "TestPlayer")
        time.sleep(0.2)
        
        # 模拟客户端超时（直接修改心跳时间）
        self.host.client.last_heartbeat = time.time() - 10.0  # 10秒前
        
        # 等待主机检测超时
        time.sleep(0.5)
        
        # 验证客户端被移除
        self.assertIsNone(self.host.client)
        self.assertEqual(self.host.get_current_player_count(), 1)

    def test_dual_player_message_validation(self):
        """测试双人游戏消息验证"""
        # 建立连接
        self.host.start_hosting("TestRoom")
        time.sleep(0.1)
        
        self.client.connect_to_host("127.0.0.1", self.host_port, "TestPlayer")
        time.sleep(0.2)
        
        # 测试有效消息处理
        valid_input = MessageFactory.create_player_input(
            self.client.player_id, ["W"], []
        )
        
        # 模拟发送有效消息
        with patch.object(self.host, '_handle_player_input') as mock_handler:
            self.host._handle_client_message(valid_input.to_bytes(), ("127.0.0.1", 12345))
            mock_handler.assert_called_once()
        
        # 测试无效消息处理（错误的玩家ID）
        invalid_input = MessageFactory.create_player_input(
            "wrong_player_id", ["W"], []
        )
        
        with patch.object(self.host, '_handle_player_input') as mock_handler:
            self.host._handle_client_message(invalid_input.to_bytes(), ("127.0.0.1", 12345))
            mock_handler.assert_called_once()  # 方法被调用但内部会验证ID

    def test_dual_player_performance_metrics(self):
        """测试双人游戏性能指标"""
        # 建立连接
        self.host.start_hosting("TestRoom")
        time.sleep(0.1)

        self.client.connect_to_host("127.0.0.1", self.host_port, "TestPlayer")
        time.sleep(0.2)

        # 测试游戏状态同步频率限制
        game_state = {
            "tanks": [{"id": "host", "x": 100, "y": 100}],
            "bullets": [],
            "round_info": {"score": [0, 0]}
        }

        # 记录实际发送次数
        original_sendto = self.host.host_socket.sendto
        actual_send_count = 0

        def count_sendto(*args, **kwargs):
            nonlocal actual_send_count
            actual_send_count += 1
            return original_sendto(*args, **kwargs)

        self.host.host_socket.sendto = count_sendto

        # 快速连续发送多个状态更新
        start_time = time.time()
        call_count = 0

        for i in range(10):
            self.host.send_game_state(game_state)
            call_count += 1
            time.sleep(0.01)  # 10ms间隔，远小于30Hz限制

        end_time = time.time()

        # 验证发送频率被正确限制
        # 在约100ms内，30Hz限制应该只允许发送3-4次
        duration = end_time - start_time
        expected_max_sends = int(duration * 30) + 2  # 加2作为容错

        print(f"调用次数: {call_count}, 实际发送次数: {actual_send_count}, 持续时间: {duration:.3f}s, 期望最大发送次数: {expected_max_sends}")

        # 验证实际发送次数被限制，而不是调用次数
        self.assertLessEqual(actual_send_count, expected_max_sends)
        self.assertLess(actual_send_count, call_count)  # 实际发送次数应该少于调用次数


if __name__ == '__main__':
    unittest.main()
