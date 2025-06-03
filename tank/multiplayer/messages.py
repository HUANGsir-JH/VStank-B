"""
网络消息协议 - 重构版

专为1对1双人游戏设计的简化消息协议
"""

import json
import time
from typing import Dict, Any, Optional
from enum import Enum


class MessageType(Enum):
    """消息类型枚举 - 简化版"""
    
    # 连接管理
    ROOM_ADVERTISE = "room_advertise"      # 房间广播
    JOIN_REQUEST = "join_request"          # 加入请求  
    JOIN_RESPONSE = "join_response"        # 加入响应
    DISCONNECT = "disconnect"              # 断开连接
    HEARTBEAT = "heartbeat"                # 心跳包
    
    # 游戏控制
    GAME_START = "game_start"              # 游戏开始
    GAME_END = "game_end"                  # 游戏结束
    GAME_STATE = "game_state"              # 游戏状态同步
    PLAYER_INPUT = "player_input"          # 玩家输入
    MAP_SYNC = "map_sync"                  # 地图同步
    
    # 坦克选择
    TANK_SELECTION_START = "tank_selection_start"    # 开始坦克选择
    TANK_SELECTED = "tank_selected"                  # 坦克选择
    TANK_SELECTION_READY = "tank_selection_ready"    # 选择完成
    TANK_SELECTION_SYNC = "tank_selection_sync"      # 选择状态同步


class NetworkMessage:
    """网络消息类 - 重构版"""
    
    def __init__(self, msg_type: MessageType, data: Dict[str, Any], 
                 player_id: Optional[str] = None):
        self.type = msg_type
        self.data = data
        self.player_id = player_id
        self.timestamp = time.time()
    
    def to_bytes(self) -> bytes:
        """序列化为字节数据"""
        msg_dict = {
            "type": self.type.value,
            "data": self.data,
            "player_id": self.player_id,
            "timestamp": self.timestamp
        }
        return json.dumps(msg_dict, ensure_ascii=False).encode('utf-8')
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'NetworkMessage':
        """从字节数据反序列化"""
        try:
            msg_dict = json.loads(data.decode('utf-8'))
            msg_type = MessageType(msg_dict["type"])
            return cls(
                msg_type,
                msg_dict["data"],
                msg_dict.get("player_id")
            )
        except (json.JSONDecodeError, KeyError, UnicodeDecodeError, ValueError) as e:
            raise ValueError(f"无效的消息格式: {e}")


class MessageFactory:
    """消息工厂类 - 简化版"""
    
    @staticmethod
    def create_room_advertise(room_name: str, host_name: str = "主机") -> NetworkMessage:
        """创建房间广播消息"""
        data = {
            "room_name": room_name,
            "host_name": host_name,
            "players": 1,  # 主机自己
            "max_players": 2,
            "game_mode": "1v1"
        }
        return NetworkMessage(MessageType.ROOM_ADVERTISE, data)
    
    @staticmethod
    def create_join_request(player_name: str) -> NetworkMessage:
        """创建加入请求"""
        data = {"player_name": player_name}
        return NetworkMessage(MessageType.JOIN_REQUEST, data)
    
    @staticmethod
    def create_join_response(success: bool, player_id: str = None, 
                           reason: str = None) -> NetworkMessage:
        """创建加入响应"""
        data = {
            "success": success,
            "player_id": player_id,
            "reason": reason
        }
        return NetworkMessage(MessageType.JOIN_RESPONSE, data)
    
    @staticmethod
    def create_disconnect(reason: str = "用户断开") -> NetworkMessage:
        """创建断开连接消息"""
        data = {"reason": reason}
        return NetworkMessage(MessageType.DISCONNECT, data)
    
    @staticmethod
    def create_heartbeat() -> NetworkMessage:
        """创建心跳包"""
        return NetworkMessage(MessageType.HEARTBEAT, {})
    
    @staticmethod
    def create_game_start(game_config: Dict[str, Any] = None) -> NetworkMessage:
        """创建游戏开始消息"""
        data = game_config or {}
        return NetworkMessage(MessageType.GAME_START, data)

    @staticmethod
    def create_map_sync(map_layout: list, map_checksum: str = None) -> NetworkMessage:
        """创建地图同步消息"""
        data = {
            "map_layout": map_layout,
            "map_checksum": map_checksum,
            "wall_count": len(map_layout)
        }
        return NetworkMessage(MessageType.MAP_SYNC, data)
    
    @staticmethod
    def create_game_state(tanks: list, bullets: list, scores: Dict[str, int] = None) -> NetworkMessage:
        """创建游戏状态消息"""
        data = {
            "tanks": tanks,
            "bullets": bullets,
            "scores": scores or {},
            "timestamp": time.time()
        }
        return NetworkMessage(MessageType.GAME_STATE, data)
    
    @staticmethod
    def create_player_input(keys_pressed: list, keys_released: list) -> NetworkMessage:
        """创建玩家输入消息"""
        data = {
            "keys_pressed": keys_pressed,
            "keys_released": keys_released
        }
        return NetworkMessage(MessageType.PLAYER_INPUT, data)
    
    @staticmethod
    def create_tank_selection_start() -> NetworkMessage:
        """创建坦克选择开始消息"""
        return NetworkMessage(MessageType.TANK_SELECTION_START, {})
    
    @staticmethod
    def create_tank_selected(tank_type: str, tank_image: str) -> NetworkMessage:
        """创建坦克选择消息"""
        data = {
            "tank_type": tank_type,
            "tank_image": tank_image
        }
        return NetworkMessage(MessageType.TANK_SELECTED, data)
    
    @staticmethod
    def create_tank_selection_ready() -> NetworkMessage:
        """创建坦克选择完成消息"""
        return NetworkMessage(MessageType.TANK_SELECTION_READY, {})
    
    @staticmethod
    def create_tank_selection_sync(selections: Dict[str, Dict[str, str]]) -> NetworkMessage:
        """创建坦克选择同步消息"""
        data = {"selections": selections}
        return NetworkMessage(MessageType.TANK_SELECTION_SYNC, data)


# 示例消息格式
EXAMPLE_MESSAGES = {
    "room_advertise": {
        "type": "room_advertise",
        "data": {
            "room_name": "玩家的房间",
            "host_name": "主机玩家",
            "players": 1,
            "max_players": 2,
            "game_mode": "1v1"
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
                    "x": 100,
                    "y": 200,
                    "angle": 45,
                    "health": 5
                },
                {
                    "player_id": "client_001", 
                    "x": 300,
                    "y": 400,
                    "angle": 180,
                    "health": 3
                }
            ],
            "bullets": [
                {
                    "x": 150,
                    "y": 250,
                    "angle": 45,
                    "owner": "host"
                }
            ],
            "scores": {
                "host": 1,
                "client_001": 0
            }
        },
        "timestamp": 1234567890.123
    }
}
