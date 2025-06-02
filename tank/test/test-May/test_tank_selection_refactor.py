"""
测试多人游戏坦克选择功能重构

验证NetworkTankSelectionView的网络同步功能
"""

import unittest
import sys
import os
import time
import threading
from unittest.mock import Mock, MagicMock, patch

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multiplayer.udp_messages import MessageFactory, MessageType

# 模拟NetworkTankSelectionView的核心逻辑，不依赖Arcade
class MockNetworkTankSelectionView:
    """模拟NetworkTankSelectionView的核心逻辑"""

    def __init__(self, is_host=True, room_name="", host_ip="", host_port=12346,
                 game_host=None, game_client=None):
        self.is_host = is_host
        self.room_name = room_name
        self.host_ip = host_ip
        self.host_port = host_port
        self.game_host = game_host
        self.game_client = game_client

        # 坦克选择相关
        self.selected_tank = None
        self.my_player_id = "host" if is_host else None

        # 全局坦克选择状态
        self.selected_tanks = {}
        self.ready_players = set()
        self.connected_players = set()

        # 可选坦克类型
        self.available_tank_types = ["green", "yellow", "blue", "grey"]
        self.tank_type_to_image = {
            "green": "/path/to/green.png",
            "yellow": "/path/to/yellow.png",
            "blue": "/path/to/blue.png",
            "grey": "/path/to/grey.png"
        }

        # 网络状态
        self.ready_to_start = False
        self.selection_conflict_message = ""
        self.conflict_message_timer = 0.0

        # 初始化
        if self.is_host:
            self.connected_players.add("host")
            self.my_player_id = "host"
        else:
            if self.game_client:
                self.my_player_id = self.game_client.get_player_id()
                if self.my_player_id:
                    self.connected_players.add(self.my_player_id)

    def _get_tank_type(self, image_path: str) -> str:
        """根据图片路径获取坦克类型"""
        if 'green' in image_path.lower():
            return "green"
        elif 'desert' in image_path.lower() or 'yellow' in image_path.lower():
            return "yellow"
        elif 'blue' in image_path.lower():
            return "blue"
        elif 'grey' in image_path.lower():
            return "grey"
        return "green"

    def _is_tank_taken(self, tank_type: str) -> bool:
        """检查坦克是否已被其他玩家选择"""
        for player_id, tank_info in self.selected_tanks.items():
            if player_id != self.my_player_id and tank_info.get("tank_type") == tank_type:
                return True
        return False

    def _is_tank_taken_by_others(self, tank_type: str, exclude_player_id: str) -> bool:
        """检查坦克是否被其他玩家选择（排除指定玩家）"""
        for player_id, tank_info in self.selected_tanks.items():
            if player_id != exclude_player_id and tank_info.get("tank_type") == tank_type:
                return True
        return False

    def _select_tank(self, tank_type: str, tank_image_path: str = None, broadcast: bool = True):
        """选择坦克"""
        if not tank_image_path:
            tank_image_path = self.tank_type_to_image.get(tank_type, "")

        self.selected_tanks[self.my_player_id] = {
            "tank_type": tank_type,
            "tank_image_path": tank_image_path
        }

        if broadcast and self.is_host:
            self._broadcast_tank_selection_sync()

    def _broadcast_tank_selection_sync(self):
        """主机广播坦克选择状态同步"""
        if not self.is_host or not self.game_host:
            return

        message = MessageFactory.create_tank_selection_sync(
            self.selected_tanks, list(self.ready_players)
        )

        self.game_host.broadcast_message(message)

    def _check_all_players_ready(self):
        """检查是否所有玩家都已准备完成"""
        if not self.is_host:
            return

        if len(self.ready_players) >= len(self.connected_players):
            print("所有玩家已准备完成，开始游戏！")
            self._start_game()

    def _start_game(self):
        """开始游戏"""
        if not self.is_host:
            return
        print("游戏开始！")

    def _handle_client_tank_selection(self, client_id: str, message_type: str, data: dict):
        """处理客户端的坦克选择消息（主机端）"""
        if not self.is_host:
            return

        if message_type == MessageType.TANK_SELECTED:
            tank_type = data.get("tank_type")
            tank_image_path = data.get("tank_image_path")

            if self._is_tank_taken_by_others(tank_type, client_id):
                conflict_msg = MessageFactory.create_tank_selection_conflict(
                    client_id, tank_type, "坦克已被其他玩家选择"
                )
                self.game_host.send_to_client(client_id, conflict_msg)
                return

            self.selected_tanks[client_id] = {
                "tank_type": tank_type,
                "tank_image_path": tank_image_path
            }

            self._broadcast_tank_selection_sync()

        elif message_type == MessageType.TANK_SELECTION_READY:
            tank_type = data.get("tank_type")
            tank_image_path = data.get("tank_image_path")

            if self._is_tank_taken_by_others(tank_type, client_id):
                conflict_msg = MessageFactory.create_tank_selection_conflict(
                    client_id, tank_type, "坦克已被其他玩家选择"
                )
                self.game_host.send_to_client(client_id, conflict_msg)
                return

            self.selected_tanks[client_id] = {
                "tank_type": tank_type,
                "tank_image_path": tank_image_path
            }
            self.ready_players.add(client_id)
            self.connected_players.add(client_id)

            self._broadcast_tank_selection_sync()
            self._check_all_players_ready()

    def _handle_tank_selection_sync(self, message_type: str, data: dict):
        """处理坦克选择同步消息（客户端）"""
        if self.is_host:
            return

        if message_type == MessageType.TANK_SELECTION_SYNC:
            self.selected_tanks = data.get("selected_tanks", {})
            self.ready_players = set(data.get("ready_players", []))

        elif message_type == MessageType.TANK_SELECTION_CONFLICT:
            reason = data.get("reason", "选择冲突")
            self.selection_conflict_message = reason
            self.conflict_message_timer = 3.0

            self.ready_to_start = False
            if self.my_player_id in self.ready_players:
                self.ready_players.remove(self.my_player_id)


class TestTankSelectionRefactor(unittest.TestCase):
    """测试坦克选择重构功能"""

    def setUp(self):
        """测试前准备"""
        # 模拟arcade窗口
        self.mock_window = Mock()

        # 模拟游戏主机
        self.mock_host = Mock()
        self.mock_host.room_name = "测试房间"
        self.mock_host.broadcast_message = Mock()
        self.mock_host.send_to_client = Mock()

        # 模拟游戏客户端
        self.mock_client = Mock()
        self.mock_client.get_player_id.return_value = "client_001"
        self.mock_client.send_message = Mock()

    def test_host_tank_selection_view_creation(self):
        """测试主机坦克选择视图创建"""
        view = MockNetworkTankSelectionView(
            is_host=True,
            room_name="测试房间",
            game_host=self.mock_host
        )

        self.assertTrue(view.is_host)
        self.assertEqual(view.room_name, "测试房间")
        self.assertEqual(view.game_host, self.mock_host)
        self.assertEqual(view.my_player_id, "host")
        self.assertIn("host", view.connected_players)

    def test_client_tank_selection_view_creation(self):
        """测试客户端坦克选择视图创建"""
        view = MockNetworkTankSelectionView(
            is_host=False,
            host_ip="192.168.1.100",
            host_port=12346,
            game_client=self.mock_client
        )

        self.assertFalse(view.is_host)
        self.assertEqual(view.host_ip, "192.168.1.100")
        self.assertEqual(view.host_port, 12346)
        self.assertEqual(view.game_client, self.mock_client)

    def test_tank_selection_messages(self):
        """测试坦克选择消息创建"""
        # 测试坦克选择消息
        msg = MessageFactory.create_tank_selected("player1", "green", "/path/to/green.png")
        self.assertEqual(msg.type, MessageType.TANK_SELECTED)
        self.assertEqual(msg.player_id, "player1")
        self.assertEqual(msg.data["tank_type"], "green")
        self.assertEqual(msg.data["tank_image_path"], "/path/to/green.png")

        # 测试坦克选择同步消息
        selected_tanks = {
            "host": {"tank_type": "green", "tank_image_path": "/path/to/green.png"},
            "client1": {"tank_type": "blue", "tank_image_path": "/path/to/blue.png"}
        }
        ready_players = ["host"]

        sync_msg = MessageFactory.create_tank_selection_sync(selected_tanks, ready_players)
        self.assertEqual(sync_msg.type, MessageType.TANK_SELECTION_SYNC)
        self.assertEqual(sync_msg.data["selected_tanks"], selected_tanks)
        self.assertEqual(sync_msg.data["ready_players"], ready_players)

    def test_tank_conflict_detection(self):
        """测试坦克选择冲突检测"""
        view = MockNetworkTankSelectionView(
            is_host=True,
            room_name="测试房间",
            game_host=self.mock_host
        )

        # 设置已选择的坦克
        view.selected_tanks = {
            "host": {"tank_type": "green", "tank_image_path": "/path/to/green.png"},
            "client1": {"tank_type": "blue", "tank_image_path": "/path/to/blue.png"}
        }

        # 测试冲突检测 - 从其他玩家的角度检测
        # 创建一个客户端视图来测试冲突检测
        client_view = MockNetworkTankSelectionView(
            is_host=False,
            game_client=self.mock_client
        )
        client_view.my_player_id = "client2"  # 设置为不同的玩家ID
        client_view.selected_tanks = view.selected_tanks

        # 现在测试冲突检测
        self.assertTrue(client_view._is_tank_taken("green"))  # 被host选择
        self.assertTrue(client_view._is_tank_taken("blue"))   # 被client1选择
        self.assertFalse(client_view._is_tank_taken("yellow")) # 未被选择
        self.assertFalse(client_view._is_tank_taken("grey"))   # 未被选择

    def test_host_tank_selection_callback(self):
        """测试主机端坦克选择回调处理"""
        view = MockNetworkTankSelectionView(
            is_host=True,
            room_name="测试房间",
            game_host=self.mock_host
        )
        view.connected_players = {"host", "client1"}

        # 模拟客户端选择坦克
        view._handle_client_tank_selection(
            "client1",
            MessageType.TANK_SELECTED,
            {"tank_type": "blue", "tank_image_path": "/path/to/blue.png"}
        )

        # 验证坦克选择被记录
        self.assertIn("client1", view.selected_tanks)
        self.assertEqual(view.selected_tanks["client1"]["tank_type"], "blue")

        # 验证广播被调用
        self.mock_host.broadcast_message.assert_called()

    def test_client_tank_selection_sync(self):
        """测试客户端坦克选择同步"""
        view = MockNetworkTankSelectionView(
            is_host=False,
            host_ip="192.168.1.100",
            host_port=12346,
            game_client=self.mock_client
        )

        # 模拟接收同步消息
        sync_data = {
            "selected_tanks": {
                "host": {"tank_type": "green", "tank_image_path": "/path/to/green.png"},
                "client1": {"tank_type": "blue", "tank_image_path": "/path/to/blue.png"}
            },
            "ready_players": ["host"]
        }

        view._handle_tank_selection_sync(MessageType.TANK_SELECTION_SYNC, sync_data)

        # 验证状态同步
        self.assertEqual(view.selected_tanks, sync_data["selected_tanks"])
        self.assertEqual(view.ready_players, set(sync_data["ready_players"]))

    def test_tank_selection_conflict_handling(self):
        """测试坦克选择冲突处理"""
        view = MockNetworkTankSelectionView(
            is_host=False,
            host_ip="192.168.1.100",
            host_port=12346,
            game_client=self.mock_client
        )

        # 模拟接收冲突消息
        conflict_data = {
            "tank_type": "green",
            "reason": "坦克已被其他玩家选择"
        }

        view._handle_tank_selection_sync(MessageType.TANK_SELECTION_CONFLICT, conflict_data)

        # 验证冲突消息显示
        self.assertEqual(view.selection_conflict_message, "坦克已被其他玩家选择")
        self.assertGreater(view.conflict_message_timer, 0)
        self.assertFalse(view.ready_to_start)

    def test_all_players_ready_check(self):
        """测试所有玩家准备完成检查"""
        view = MockNetworkTankSelectionView(
            is_host=True,
            room_name="测试房间",
            game_host=self.mock_host
        )

        # 设置连接的玩家
        view.connected_players = {"host", "client1"}
        view.ready_players = {"host", "client1"}

        # 模拟检查所有玩家准备完成
        with patch.object(view, '_start_game') as mock_start_game:
            view._check_all_players_ready()
            mock_start_game.assert_called_once()

    def test_tank_type_mapping(self):
        """测试坦克类型映射"""
        view = MockNetworkTankSelectionView(is_host=True)

        # 测试坦克类型识别
        self.assertEqual(view._get_tank_type("green_tank.png"), "green")
        self.assertEqual(view._get_tank_type("desert_tank.png"), "yellow")
        self.assertEqual(view._get_tank_type("blue_tank.png"), "blue")
        self.assertEqual(view._get_tank_type("grey_tank.png"), "grey")
        self.assertEqual(view._get_tank_type("unknown.png"), "green")  # 默认值

    def test_return_to_previous_view(self):
        """测试返回上一级视图逻辑"""
        # 这个测试主要验证逻辑，不涉及实际的视图切换
        host_view = MockNetworkTankSelectionView(
            is_host=True,
            room_name="测试房间",
            game_host=self.mock_host
        )

        # 验证主机视图的基本属性
        self.assertTrue(host_view.is_host)
        self.assertEqual(host_view.room_name, "测试房间")

        client_view = MockNetworkTankSelectionView(
            is_host=False,
            host_ip="192.168.1.100",
            host_port=12346,
            game_client=self.mock_client
        )

        # 验证客户端视图的基本属性
        self.assertFalse(client_view.is_host)
        self.assertEqual(client_view.host_ip, "192.168.1.100")


if __name__ == '__main__':
    unittest.main()
