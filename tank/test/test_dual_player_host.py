"""
双人游戏主机端单元测试

测试重构后的双人游戏主机功能，确保只支持1个客户端连接
"""

import unittest
import time
import threading
from unittest.mock import Mock, patch
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from multiplayer.dual_player_host import DualPlayerHost, ClientInfo
from multiplayer.udp_messages import MessageFactory, MessageType


class TestClientInfo(unittest.TestCase):
    """测试客户端信息类"""

    def setUp(self):
        self.client_info = ClientInfo("test_client", ("127.0.0.1", 12346), "TestPlayer")

    def test_client_info_initialization(self):
        """测试客户端信息初始化"""
        self.assertEqual(self.client_info.client_id, "test_client")
        self.assertEqual(self.client_info.address, ("127.0.0.1", 12346))
        self.assertEqual(self.client_info.player_name, "TestPlayer")
        self.assertTrue(self.client_info.connected)
        self.assertEqual(len(self.client_info.current_keys), 0)

    def test_heartbeat_update(self):
        """测试心跳更新"""
        initial_time = self.client_info.last_heartbeat
        time.sleep(0.01)  # 等待一小段时间
        self.client_info.update_heartbeat()
        self.assertGreater(self.client_info.last_heartbeat, initial_time)

    def test_timeout_check(self):
        """测试超时检查"""
        # 正常情况下不应该超时
        self.assertFalse(self.client_info.is_timeout(timeout=1.0))
        
        # 模拟超时
        self.client_info.last_heartbeat = time.time() - 5.0
        self.assertTrue(self.client_info.is_timeout(timeout=3.0))

    def test_input_update(self):
        """测试输入状态更新"""
        # 测试按键按下
        self.client_info.update_input(["W", "A"], [])
        self.assertIn("W", self.client_info.current_keys)
        self.assertIn("A", self.client_info.current_keys)

        # 测试按键释放
        self.client_info.update_input(["S"], ["A"])
        self.assertIn("W", self.client_info.current_keys)
        self.assertIn("S", self.client_info.current_keys)
        self.assertNotIn("A", self.client_info.current_keys)


class TestDualPlayerHost(unittest.TestCase):
    """测试双人游戏主机类"""

    def setUp(self):
        self.host = DualPlayerHost(host_port=12347)  # 使用不同端口避免冲突

    def tearDown(self):
        if self.host.running:
            self.host.stop_hosting(force=True)

    def test_host_initialization(self):
        """测试主机初始化"""
        self.assertEqual(self.host.host_port, 12347)
        self.assertEqual(self.host.max_players, 2)
        self.assertFalse(self.host.running)
        self.assertIsNone(self.host.client)
        self.assertEqual(self.host.host_player_id, "host")

    def test_player_count(self):
        """测试玩家数量计算"""
        # 只有主机
        self.assertEqual(self.host.get_current_player_count(), 1)
        
        # 添加客户端
        self.host.client = ClientInfo("test_client", ("127.0.0.1", 12346), "TestPlayer")
        self.assertEqual(self.host.get_current_player_count(), 2)
        
        # 客户端断开连接
        self.host.client.connected = False
        self.assertEqual(self.host.get_current_player_count(), 1)

    def test_room_full_check(self):
        """测试房间满员检查"""
        # 房间未满
        self.assertFalse(self.host.is_room_full())
        
        # 添加客户端后房间满员
        self.host.client = ClientInfo("test_client", ("127.0.0.1", 12346), "TestPlayer")
        self.assertTrue(self.host.is_room_full())

    def test_connected_players(self):
        """测试连接的玩家列表"""
        # 只有主机
        players = self.host.get_connected_players()
        self.assertEqual(players, ["host"])
        
        # 添加客户端
        self.host.client = ClientInfo("test_client", ("127.0.0.1", 12346), "TestPlayer")
        players = self.host.get_connected_players()
        self.assertEqual(set(players), {"host", "test_client"})

    def test_client_input_retrieval(self):
        """测试客户端输入获取"""
        # 无客户端时返回空集合
        input_keys = self.host.get_client_input()
        self.assertEqual(input_keys, set())
        
        # 有客户端时返回其输入
        self.host.client = ClientInfo("test_client", ("127.0.0.1", 12346), "TestPlayer")
        self.host.client.current_keys = {"W", "SPACE"}
        input_keys = self.host.get_client_input()
        self.assertEqual(input_keys, {"W", "SPACE"})

    def test_client_id_retrieval(self):
        """测试客户端ID获取"""
        # 无客户端时返回None
        self.assertIsNone(self.host.get_client_id())
        
        # 有客户端时返回其ID
        self.host.client = ClientInfo("test_client", ("127.0.0.1", 12346), "TestPlayer")
        self.assertEqual(self.host.get_client_id(), "test_client")

    @patch('socket.socket')
    def test_start_hosting_success(self, mock_socket):
        """测试成功启动主机"""
        # 模拟套接字
        mock_sock = Mock()
        mock_socket.return_value = mock_sock
        
        # 模拟房间广播器
        self.host.room_advertiser = Mock()
        
        result = self.host.start_hosting("TestRoom")
        
        self.assertTrue(result)
        self.assertTrue(self.host.running)
        self.assertEqual(self.host.room_name, "TestRoom")
        
        # 验证套接字配置
        mock_sock.setsockopt.assert_called()
        mock_sock.bind.assert_called_with(('', 12347))
        mock_sock.settimeout.assert_called_with(0.1)
        
        # 验证房间广播启动
        self.host.room_advertiser.start_advertising.assert_called_once()

    def test_callback_setting(self):
        """测试回调函数设置"""
        join_callback = Mock()
        leave_callback = Mock()
        input_callback = Mock()
        game_state_callback = Mock()
        tank_selection_callback = Mock()
        
        self.host.set_callbacks(
            client_join=join_callback,
            client_leave=leave_callback,
            input_received=input_callback,
            game_state=game_state_callback
        )
        
        self.host.set_tank_selection_callback(tank_selection_callback)
        
        self.assertEqual(self.host.client_join_callback, join_callback)
        self.assertEqual(self.host.client_leave_callback, leave_callback)
        self.assertEqual(self.host.input_received_callback, input_callback)
        self.assertEqual(self.host.game_state_callback, game_state_callback)
        self.assertEqual(self.host.tank_selection_callback, tank_selection_callback)

    def test_game_state_sync_timing(self):
        """测试游戏状态同步时机"""
        # 模拟客户端
        self.host.client = ClientInfo("test_client", ("127.0.0.1", 12346), "TestPlayer")
        self.host.host_socket = Mock()
        
        game_state = {
            "tanks": [{"id": "host", "x": 100, "y": 100}],
            "bullets": [],
            "round_info": {"score": [0, 0]}
        }
        
        # 第一次发送应该成功
        self.host.send_game_state(game_state)
        self.host.host_socket.sendto.assert_called_once()
        
        # 立即再次发送应该被限制（30Hz限制）
        self.host.host_socket.reset_mock()
        self.host.send_game_state(game_state)
        self.host.host_socket.sendto.assert_not_called()


if __name__ == '__main__':
    unittest.main()
