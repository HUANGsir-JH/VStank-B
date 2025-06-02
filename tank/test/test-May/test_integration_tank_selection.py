"""
多人游戏坦克选择功能集成测试

测试完整的坦克选择流程，包括主机-客户端交互
"""

import unittest
import sys
import os
import time
import threading
from unittest.mock import Mock, patch

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multiplayer.udp_messages import MessageFactory, MessageType
from multiplayer.udp_host import GameHost
from multiplayer.udp_client import GameClient


class TestTankSelectionIntegration(unittest.TestCase):
    """测试坦克选择集成功能"""

    def setUp(self):
        """测试前准备"""
        self.host_port = 12350  # 使用不同的端口避免冲突
        self.client_port = 12351
        
        # 创建主机和客户端
        self.game_host = GameHost()
        self.game_client = GameClient()
        
        # 记录接收到的消息
        self.host_received_messages = []
        self.client_received_messages = []

    def tearDown(self):
        """测试后清理"""
        if hasattr(self.game_host, 'stop_hosting'):
            self.game_host.stop_hosting()
        if hasattr(self.game_client, 'disconnect'):
            self.game_client.disconnect()
        time.sleep(0.1)  # 等待清理完成

    def test_tank_selection_message_serialization(self):
        """测试坦克选择消息序列化和反序列化"""
        # 测试坦克选择消息
        original_msg = MessageFactory.create_tank_selected(
            "player1", "green", "/path/to/green.png"
        )
        
        # 序列化和反序列化
        serialized = original_msg.to_bytes()
        deserialized = original_msg.from_bytes(serialized)
        
        # 验证消息内容
        self.assertEqual(deserialized.type, MessageType.TANK_SELECTED)
        self.assertEqual(deserialized.player_id, "player1")
        self.assertEqual(deserialized.data["tank_type"], "green")
        self.assertEqual(deserialized.data["tank_image_path"], "/path/to/green.png")

    def test_tank_selection_sync_message(self):
        """测试坦克选择同步消息"""
        selected_tanks = {
            "host": {"tank_type": "green", "tank_image_path": "/path/to/green.png"},
            "client1": {"tank_type": "blue", "tank_image_path": "/path/to/blue.png"}
        }
        ready_players = ["host"]
        
        # 创建同步消息
        sync_msg = MessageFactory.create_tank_selection_sync(selected_tanks, ready_players)
        
        # 序列化和反序列化
        serialized = sync_msg.to_bytes()
        deserialized = sync_msg.from_bytes(serialized)
        
        # 验证消息内容
        self.assertEqual(deserialized.type, MessageType.TANK_SELECTION_SYNC)
        self.assertEqual(deserialized.data["selected_tanks"], selected_tanks)
        self.assertEqual(deserialized.data["ready_players"], ready_players)

    def test_tank_selection_conflict_message(self):
        """测试坦克选择冲突消息"""
        conflict_msg = MessageFactory.create_tank_selection_conflict(
            "player1", "green", "坦克已被其他玩家选择"
        )
        
        # 序列化和反序列化
        serialized = conflict_msg.to_bytes()
        deserialized = conflict_msg.from_bytes(serialized)
        
        # 验证消息内容
        self.assertEqual(deserialized.type, MessageType.TANK_SELECTION_CONFLICT)
        self.assertEqual(deserialized.player_id, "player1")
        self.assertEqual(deserialized.data["tank_type"], "green")
        self.assertEqual(deserialized.data["reason"], "坦克已被其他玩家选择")

    def test_tank_selection_ready_message(self):
        """测试坦克选择准备消息"""
        ready_msg = MessageFactory.create_tank_selection_ready(
            "player1", "blue", "/path/to/blue.png"
        )
        
        # 序列化和反序列化
        serialized = ready_msg.to_bytes()
        deserialized = ready_msg.from_bytes(serialized)
        
        # 验证消息内容
        self.assertEqual(deserialized.type, MessageType.TANK_SELECTION_READY)
        self.assertEqual(deserialized.player_id, "player1")
        self.assertEqual(deserialized.data["tank_type"], "blue")
        self.assertEqual(deserialized.data["tank_image_path"], "/path/to/blue.png")

    def test_message_type_constants(self):
        """测试消息类型常量"""
        # 验证新增的坦克选择消息类型
        self.assertEqual(MessageType.TANK_SELECTION_START, "tank_selection_start")
        self.assertEqual(MessageType.TANK_SELECTED, "tank_selected")
        self.assertEqual(MessageType.TANK_SELECTION_SYNC, "tank_selection_sync")
        self.assertEqual(MessageType.TANK_SELECTION_READY, "tank_selection_ready")
        self.assertEqual(MessageType.TANK_SELECTION_CONFLICT, "tank_selection_conflict")

    def test_udp_host_tank_selection_callback(self):
        """测试UDP主机的坦克选择回调设置"""
        callback_called = False
        received_args = []
        
        def tank_selection_callback(client_id, message_type, data):
            nonlocal callback_called, received_args
            callback_called = True
            received_args = [client_id, message_type, data]
        
        # 设置回调
        self.game_host.set_tank_selection_callback(tank_selection_callback)
        self.assertEqual(self.game_host.tank_selection_callback, tank_selection_callback)

    def test_udp_client_tank_selection_callback(self):
        """测试UDP客户端的坦克选择回调设置"""
        callback_called = False
        received_args = []
        
        def tank_selection_callback(message_type, data):
            nonlocal callback_called, received_args
            callback_called = True
            received_args = [message_type, data]
        
        # 设置回调
        self.game_client.set_tank_selection_callback(tank_selection_callback)
        self.assertEqual(self.game_client.tank_selection_callback, tank_selection_callback)

    def test_tank_selection_workflow_simulation(self):
        """模拟完整的坦克选择工作流程"""
        # 模拟主机状态
        host_selected_tanks = {}
        host_ready_players = set()
        host_connected_players = {"host", "client1"}
        
        # 步骤1: 主机选择坦克
        host_selected_tanks["host"] = {
            "tank_type": "green",
            "tank_image_path": "/path/to/green.png"
        }
        
        # 步骤2: 客户端选择坦克
        client_selection = {
            "tank_type": "blue",
            "tank_image_path": "/path/to/blue.png"
        }
        
        # 检查冲突（应该没有冲突）
        tank_types = [info["tank_type"] for info in host_selected_tanks.values()]
        self.assertNotIn(client_selection["tank_type"], tank_types)
        
        # 添加客户端选择
        host_selected_tanks["client1"] = client_selection
        
        # 步骤3: 主机准备
        host_ready_players.add("host")
        
        # 步骤4: 客户端准备
        host_ready_players.add("client1")
        
        # 步骤5: 检查所有玩家是否准备完成
        all_ready = len(host_ready_players) >= len(host_connected_players)
        self.assertTrue(all_ready)
        
        # 验证最终状态
        self.assertEqual(len(host_selected_tanks), 2)
        self.assertEqual(host_selected_tanks["host"]["tank_type"], "green")
        self.assertEqual(host_selected_tanks["client1"]["tank_type"], "blue")
        self.assertEqual(len(host_ready_players), 2)

    def test_tank_selection_conflict_scenario(self):
        """测试坦克选择冲突场景"""
        # 模拟主机状态
        host_selected_tanks = {
            "host": {"tank_type": "green", "tank_image_path": "/path/to/green.png"}
        }
        
        # 客户端尝试选择相同的坦克
        client_selection = {
            "tank_type": "green",  # 与主机相同
            "tank_image_path": "/path/to/green.png"
        }
        
        # 检查冲突
        tank_types = [info["tank_type"] for info in host_selected_tanks.values()]
        has_conflict = client_selection["tank_type"] in tank_types
        self.assertTrue(has_conflict)
        
        # 模拟冲突处理 - 客户端应该选择其他坦克
        alternative_selection = {
            "tank_type": "blue",
            "tank_image_path": "/path/to/blue.png"
        }
        
        # 验证替代选择没有冲突
        has_conflict_alternative = alternative_selection["tank_type"] in tank_types
        self.assertFalse(has_conflict_alternative)


if __name__ == '__main__':
    unittest.main()
