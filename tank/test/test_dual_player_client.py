"""
双人游戏客户端单元测试

测试重构后的双人游戏客户端功能
"""

import unittest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from multiplayer.dual_player_client import DualPlayerClient
from multiplayer.udp_messages import MessageFactory, MessageType, UDPMessage


class TestDualPlayerClient(unittest.TestCase):
    """测试双人游戏客户端类"""

    def setUp(self):
        self.client = DualPlayerClient()

    def tearDown(self):
        if self.client.connected:
            self.client.disconnect()

    def test_client_initialization(self):
        """测试客户端初始化"""
        self.assertIsNone(self.client.client_socket)
        self.assertIsNone(self.client.host_address)
        self.assertFalse(self.client.running)
        self.assertIsNone(self.client.player_id)
        self.assertEqual(self.client.player_name, "")
        self.assertFalse(self.client.connected)
        self.assertEqual(len(self.client.current_keys), 0)
        self.assertEqual(len(self.client.pending_key_presses), 0)
        self.assertEqual(len(self.client.pending_key_releases), 0)

    def test_callback_setting(self):
        """测试回调函数设置"""
        connection_callback = Mock()
        disconnection_callback = Mock()
        game_state_callback = Mock()
        tank_selection_callback = Mock()
        
        self.client.set_callbacks(
            connection=connection_callback,
            disconnection=disconnection_callback,
            game_state=game_state_callback
        )
        
        self.client.set_tank_selection_callback(tank_selection_callback)
        
        self.assertEqual(self.client.connection_callback, connection_callback)
        self.assertEqual(self.client.disconnection_callback, disconnection_callback)
        self.assertEqual(self.client.game_state_callback, game_state_callback)
        self.assertEqual(self.client.tank_selection_callback, tank_selection_callback)

    def test_key_input_handling(self):
        """测试按键输入处理"""
        # 模拟连接状态
        self.client.connected = True
        
        # 测试按键按下
        self.client.send_key_press("W")
        self.assertIn("W", self.client.current_keys)
        self.assertIn("W", self.client.pending_key_presses)
        
        # 测试重复按键按下（应该被忽略）
        self.client.send_key_press("W")
        self.assertEqual(self.client.pending_key_presses.count("W"), 1)
        
        # 测试按键释放
        self.client.send_key_release("W")
        self.assertNotIn("W", self.client.current_keys)
        self.assertIn("W", self.client.pending_key_releases)
        
        # 测试释放未按下的按键（应该被忽略）
        self.client.send_key_release("A")
        self.assertNotIn("A", self.client.pending_key_releases)

    def test_key_input_when_disconnected(self):
        """测试断开连接时的按键输入处理"""
        # 确保未连接
        self.client.connected = False
        
        # 尝试发送按键，应该被忽略
        self.client.send_key_press("W")
        self.assertEqual(len(self.client.current_keys), 0)
        self.assertEqual(len(self.client.pending_key_presses), 0)
        
        self.client.send_key_release("W")
        self.assertEqual(len(self.client.pending_key_releases), 0)

    def test_connection_status_methods(self):
        """测试连接状态相关方法"""
        # 初始状态
        self.assertFalse(self.client.is_connected())
        self.assertIsNone(self.client.get_player_id())
        
        # 模拟连接
        self.client.connected = True
        self.client.player_id = "test_player"
        
        self.assertTrue(self.client.is_connected())
        self.assertEqual(self.client.get_player_id(), "test_player")

    def test_current_keys_retrieval(self):
        """测试当前按键状态获取"""
        self.client.connected = True
        
        # 添加一些按键
        self.client.send_key_press("W")
        self.client.send_key_press("SPACE")
        
        current_keys = self.client.get_current_keys()
        self.assertEqual(current_keys, {"W", "SPACE"})
        
        # 确保返回的是副本，不会影响原始数据
        current_keys.add("A")
        self.assertNotIn("A", self.client.current_keys)

    @patch('socket.socket')
    def test_successful_connection(self, mock_socket):
        """测试成功连接到主机"""
        # 模拟套接字
        mock_sock = Mock()
        mock_socket.return_value = mock_sock
        
        # 模拟成功的连接响应
        success_response = MessageFactory.create_join_response(True, "test_player_id")
        mock_sock.recvfrom.return_value = (success_response.to_bytes(), ("127.0.0.1", 12346))
        
        # 模拟连接回调
        connection_callback = Mock()
        self.client.set_callbacks(connection=connection_callback)
        
        # 尝试连接
        result = self.client.connect_to_host("127.0.0.1", 12346, "TestPlayer")
        
        self.assertTrue(result)
        self.assertTrue(self.client.connected)
        self.assertEqual(self.client.player_id, "test_player_id")
        self.assertEqual(self.client.player_name, "TestPlayer")
        self.assertEqual(self.client.host_address, ("127.0.0.1", 12346))
        
        # 验证连接回调被调用
        connection_callback.assert_called_once_with("test_player_id")

    @patch('socket.socket')
    def test_failed_connection(self, mock_socket):
        """测试连接失败"""
        # 模拟套接字
        mock_sock = Mock()
        mock_socket.return_value = mock_sock
        
        # 模拟失败的连接响应
        failure_response = MessageFactory.create_join_response(False, reason="房间已满")
        mock_sock.recvfrom.return_value = (failure_response.to_bytes(), ("127.0.0.1", 12346))
        
        # 尝试连接
        result = self.client.connect_to_host("127.0.0.1", 12346, "TestPlayer")
        
        self.assertFalse(result)
        self.assertFalse(self.client.connected)
        self.assertIsNone(self.client.player_id)

    @patch('socket.socket')
    def test_connection_exception(self, mock_socket):
        """测试连接异常处理"""
        # 模拟套接字异常
        mock_socket.side_effect = Exception("Network error")
        
        # 尝试连接
        result = self.client.connect_to_host("127.0.0.1", 12346, "TestPlayer")
        
        self.assertFalse(result)
        self.assertFalse(self.client.connected)

    def test_disconnect_cleanup(self):
        """测试断开连接时的清理工作"""
        # 模拟连接状态
        self.client.connected = True
        self.client.player_id = "test_player"
        self.client.host_address = ("127.0.0.1", 12346)
        self.client.client_socket = Mock()
        self.client.current_keys = {"W", "SPACE"}
        self.client.pending_key_presses = ["A"]
        self.client.pending_key_releases = ["S"]
        
        # 设置断开连接回调
        disconnection_callback = Mock()
        self.client.set_callbacks(disconnection=disconnection_callback)
        
        # 断开连接
        self.client.disconnect()
        
        # 验证清理工作
        self.assertFalse(self.client.connected)
        self.assertFalse(self.client.running)
        self.assertIsNone(self.client.player_id)
        self.assertIsNone(self.client.host_address)
        self.assertEqual(len(self.client.current_keys), 0)
        self.assertEqual(len(self.client.pending_key_presses), 0)
        self.assertEqual(len(self.client.pending_key_releases), 0)
        
        # 验证断开连接回调被调用
        disconnection_callback.assert_called_once_with("user_disconnect")

    def test_send_message_when_connected(self):
        """测试连接时发送消息"""
        # 模拟连接状态
        self.client.connected = True
        self.client.client_socket = Mock()
        self.client.host_address = ("127.0.0.1", 12346)
        
        # 发送消息
        test_message = MessageFactory.create_heartbeat("test_player")
        self.client.send_message(test_message)
        
        # 验证消息被发送
        self.client.client_socket.sendto.assert_called_once()

    def test_send_message_when_disconnected(self):
        """测试断开连接时发送消息"""
        # 确保未连接
        self.client.connected = False
        self.client.client_socket = Mock()
        
        # 尝试发送消息
        test_message = MessageFactory.create_heartbeat("test_player")
        self.client.send_message(test_message)
        
        # 验证消息未被发送
        self.client.client_socket.sendto.assert_not_called()

    def test_handle_game_state_message(self):
        """测试游戏状态消息处理"""
        # 设置游戏状态回调
        game_state_callback = Mock()
        self.client.set_callbacks(game_state=game_state_callback)
        
        # 模拟游戏状态消息
        game_state_data = {
            "tanks": [{"id": "host", "x": 100, "y": 100}],
            "bullets": [],
            "round_info": {"score": [0, 0]}
        }
        
        message_data = game_state_data
        
        # 调用消息处理方法
        self.client._handle_server_message(
            MessageFactory.create_game_state(
                game_state_data["tanks"],
                game_state_data["bullets"],
                game_state_data["round_info"]
            ).to_bytes()
        )
        
        # 验证回调被调用
        game_state_callback.assert_called_once()

    def test_handle_disconnect_message(self):
        """测试断开连接消息处理"""
        # 模拟连接状态
        self.client.connected = True
        
        # 设置断开连接回调
        disconnection_callback = Mock()
        self.client.set_callbacks(disconnection=disconnection_callback)
        
        # 模拟服务器断开连接消息
        disconnect_message = MessageFactory.create_disconnect("host", "server_shutdown")
        
        # 调用消息处理方法
        self.client._handle_server_message(disconnect_message.to_bytes())
        
        # 验证连接状态被更新
        self.assertFalse(self.client.connected)


if __name__ == '__main__':
    unittest.main()
