"""
UDP消息协议定义

定义了多人游戏中使用的所有消息类型和格式
"""

import json
import time
from typing import Dict, Any, Optional
from enum import Enum


class MessageType:
    """消息类型常量"""
    ROOM_ADVERTISE = "room_advertise"    # 房间广播
    JOIN_REQUEST = "join_request"        # 加入请求
    JOIN_RESPONSE = "join_response"      # 加入响应
    PLAYER_INPUT = "player_input"        # 玩家输入
    GAME_STATE = "game_state"           # 游戏状态
    PLAYER_DISCONNECT = "disconnect"     # 玩家断线
    HEARTBEAT = "heartbeat"             # 心跳包
    GAME_START = "game_start"           # 游戏开始
    GAME_END = "game_end"               # 游戏结束

    # 坦克选择相关消息
    TANK_SELECTION_START = "tank_selection_start"    # 开始坦克选择
    TANK_SELECTED = "tank_selected"                  # 玩家选择坦克
    TANK_SELECTION_SYNC = "tank_selection_sync"      # 坦克选择状态同步
    TANK_SELECTION_READY = "tank_selection_ready"    # 玩家准备完成
    TANK_SELECTION_CONFLICT = "tank_selection_conflict"  # 坦克选择冲突


class UDPMessage:
    """UDP消息封装类"""

    def __init__(self, msg_type: str, data: Dict[str, Any], player_id: Optional[str] = None):
        self.type = msg_type
        self.data = data
        self.player_id = player_id
        self.timestamp = time.time()

    def to_bytes(self) -> bytes:
        """将消息转换为字节数据"""
        msg_dict = {
            "type": self.type,
            "data": self.data,
            "player_id": self.player_id,
            "timestamp": self.timestamp
        }
        return json.dumps(msg_dict).encode('utf-8')

    @classmethod
    def from_bytes(cls, data: bytes) -> 'UDPMessage':
        """从字节数据创建消息对象"""
        try:
            msg_dict = json.loads(data.decode('utf-8'))
            return cls(
                msg_dict["type"],
                msg_dict["data"],
                msg_dict.get("player_id")
            )
        except (json.JSONDecodeError, KeyError, UnicodeDecodeError) as e:
            raise ValueError(f"Invalid message format: {e}")


class MessageFactory:
    """消息工厂类，用于创建标准格式的消息"""

    @staticmethod
    def create_room_advertise(room_name: str, current_players: int, max_players: int,
                            game_mode: str = "pvp") -> UDPMessage:
        """创建房间广播消息"""
        data = {
            "room_name": room_name,
            "current_players": current_players,
            "max_players": max_players,
            "game_mode": game_mode
        }
        return UDPMessage(MessageType.ROOM_ADVERTISE, data)

    @staticmethod
    def create_join_request(player_name: str) -> UDPMessage:
        """创建加入房间请求"""
        data = {"player_name": player_name}
        return UDPMessage(MessageType.JOIN_REQUEST, data)

    @staticmethod
    def create_join_response(success: bool, player_id: str = None,
                           reason: str = None) -> UDPMessage:
        """创建加入房间响应"""
        data = {
            "success": success,
            "player_id": player_id,
            "reason": reason
        }
        return UDPMessage(MessageType.JOIN_RESPONSE, data)

    @staticmethod
    def create_player_input(player_id: str, keys_pressed: list,
                          keys_released: list = None) -> UDPMessage:
        """创建玩家输入消息"""
        data = {
            "keys_pressed": keys_pressed,
            "keys_released": keys_released or []
        }
        return UDPMessage(MessageType.PLAYER_INPUT, data, player_id)

    @staticmethod
    def create_game_state(tanks: list, bullets: list, round_info: dict) -> UDPMessage:
        """创建游戏状态消息"""
        data = {
            "tanks": tanks,
            "bullets": bullets,
            "round_info": round_info
        }
        return UDPMessage(MessageType.GAME_STATE, data)

    @staticmethod
    def create_heartbeat(player_id: str) -> UDPMessage:
        """创建心跳消息"""
        return UDPMessage(MessageType.HEARTBEAT, {}, player_id)

    @staticmethod
    def create_disconnect(player_id: str, reason: str = "user_quit") -> UDPMessage:
        """创建断线消息"""
        data = {"reason": reason}
        return UDPMessage(MessageType.PLAYER_DISCONNECT, data, player_id)

    # 坦克选择相关消息工厂方法
    @staticmethod
    def create_tank_selection_start() -> UDPMessage:
        """创建开始坦克选择消息"""
        return UDPMessage(MessageType.TANK_SELECTION_START, {})

    @staticmethod
    def create_tank_selected(player_id: str, tank_type: str, tank_image_path: str) -> UDPMessage:
        """创建玩家选择坦克消息"""
        data = {
            "tank_type": tank_type,
            "tank_image_path": tank_image_path
        }
        return UDPMessage(MessageType.TANK_SELECTED, data, player_id)

    @staticmethod
    def create_tank_selection_sync(selected_tanks: Dict[str, Dict[str, str]],
                                 ready_players: list) -> UDPMessage:
        """创建坦克选择状态同步消息"""
        data = {
            "selected_tanks": selected_tanks,  # {player_id: {"tank_type": str, "tank_image_path": str}}
            "ready_players": ready_players
        }
        return UDPMessage(MessageType.TANK_SELECTION_SYNC, data)

    @staticmethod
    def create_tank_selection_ready(player_id: str, tank_type: str, tank_image_path: str) -> UDPMessage:
        """创建玩家准备完成消息"""
        data = {
            "tank_type": tank_type,
            "tank_image_path": tank_image_path
        }
        return UDPMessage(MessageType.TANK_SELECTION_READY, data, player_id)

    @staticmethod
    def create_tank_selection_conflict(player_id: str, tank_type: str, reason: str) -> UDPMessage:
        """创建坦克选择冲突消息"""
        data = {
            "tank_type": tank_type,
            "reason": reason
        }
        return UDPMessage(MessageType.TANK_SELECTION_CONFLICT, data, player_id)


# 示例消息格式（用于文档和测试）
EXAMPLE_MESSAGES = {
    "room_advertise": {
        "type": "room_advertise",
        "data": {
            "room_name": "Player1's Room",
            "current_players": 1,
            "max_players": 4,
            "game_mode": "pvp"
        },
        "timestamp": 1234567890.123
    },

    "player_input": {
        "type": "player_input",
        "player_id": "client_001",
        "data": {
            "keys_pressed": ["W", "SPACE"],
            "keys_released": ["A"]
        },
        "timestamp": 1234567890.123
    },

    "game_state": {
        "type": "game_state",
        "data": {
            "tanks": [
                {
                    "player_id": "host",
                    "position": [100, 200],
                    "angle": 45,
                    "health": 5,
                    "tank_image": "green_tank.png"
                }
            ],
            "bullets": [
                {
                    "id": "bullet_1",
                    "position": [150, 250],
                    "angle": 45,
                    "owner": "host"
                }
            ],
            "round_info": {
                "scores": {"host": 1, "client_001": 0},
                "round_over": False,
                "game_over": False,
                "winner": None
            }
        },
        "timestamp": 1234567890.123
    }
}
