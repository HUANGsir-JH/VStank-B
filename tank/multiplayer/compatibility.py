"""
双人联机模块兼容性层

为了帮助现有代码平滑迁移到新的双人模式，提供旧API的兼容性包装
"""

import warnings
from typing import Dict, List, Optional, Callable
from .dual_player_host import DualPlayerHost, ClientInfo
from .dual_player_client import DualPlayerClient


class GameHost:
    """
    旧版GameHost的兼容性包装器
    
    警告：这是一个兼容性层，建议迁移到DualPlayerHost
    """
    
    def __init__(self, host_port: int = 12346, max_players: int = 4):
        warnings.warn(
            "GameHost已弃用，请使用DualPlayerHost。"
            "新版本只支持双人模式（max_players=2）。",
            DeprecationWarning,
            stacklevel=2
        )
        
        if max_players > 2:
            warnings.warn(
                f"max_players={max_players}不被支持，已自动设置为2（双人模式）",
                UserWarning,
                stacklevel=2
            )
        
        self._dual_host = DualPlayerHost(host_port)
        self.host_port = host_port
        self.max_players = 2  # 强制设为2
        
        # 兼容性属性
        self.running = False
        self.host_player_id = "host"
        
    @property
    def clients(self) -> Dict[str, ClientInfo]:
        """兼容性属性：模拟旧版的clients字典"""
        if self._dual_host.client:
            return {self._dual_host.client.client_id: self._dual_host.client}
        return {}
    
    def set_callbacks(self, client_join: Callable = None, client_leave: Callable = None,
                     input_received: Callable = None, game_state: Callable = None):
        """设置回调函数（兼容性方法）"""
        self._dual_host.set_callbacks(client_join, client_leave, input_received, game_state)
    
    def set_tank_selection_callback(self, callback: Callable):
        """设置坦克选择回调函数（兼容性方法）"""
        self._dual_host.set_tank_selection_callback(callback)
    
    def start_hosting(self, room_name: str) -> bool:
        """开始主机服务（兼容性方法）"""
        result = self._dual_host.start_hosting(room_name)
        self.running = self._dual_host.running
        return result
    
    def stop_hosting(self, force=False):
        """停止主机服务（兼容性方法）"""
        result = self._dual_host.stop_hosting(force)
        self.running = self._dual_host.running
        return result
    
    def get_current_player_count(self) -> int:
        """获取当前玩家数量（兼容性方法）"""
        return self._dual_host.get_current_player_count()
    
    def get_connected_players(self) -> List[str]:
        """获取所有连接的玩家ID（兼容性方法）"""
        return self._dual_host.get_connected_players()
    
    def broadcast_game_state(self, game_state_data: dict):
        """广播游戏状态（兼容性方法，实际为点对点发送）"""
        warnings.warn(
            "broadcast_game_state已弃用，请使用send_game_state。"
            "双人模式下使用点对点发送替代广播。",
            DeprecationWarning,
            stacklevel=2
        )
        self._dual_host.send_game_state(game_state_data)
    
    def send_game_state(self, game_state_data: dict):
        """发送游戏状态（推荐方法）"""
        self._dual_host.send_game_state(game_state_data)
    
    def broadcast_message(self, message):
        """广播消息（兼容性方法，实际为点对点发送）"""
        warnings.warn(
            "broadcast_message已弃用，请使用send_to_client。"
            "双人模式下使用点对点发送替代广播。",
            DeprecationWarning,
            stacklevel=2
        )
        self._dual_host.send_to_client(message)
    
    def send_to_client(self, client_id_or_message, message=None):
        """
        发送消息给客户端（兼容性方法）
        
        支持两种调用方式：
        1. send_to_client(client_id, message) - 旧版API
        2. send_to_client(message) - 新版API
        """
        if message is None:
            # 新版API：send_to_client(message)
            self._dual_host.send_to_client(client_id_or_message)
        else:
            # 旧版API：send_to_client(client_id, message)
            warnings.warn(
                "send_to_client(client_id, message)已弃用，请使用send_to_client(message)。"
                "双人模式下不需要指定client_id。",
                DeprecationWarning,
                stacklevel=2
            )
            self._dual_host.send_to_client(message)
    
    def get_client_input(self, client_id: str = None) -> set:
        """
        获取客户端当前输入状态（兼容性方法）
        
        参数client_id在双人模式下被忽略
        """
        if client_id is not None:
            warnings.warn(
                "get_client_input(client_id)已弃用，请使用get_client_input()。"
                "双人模式下不需要指定client_id。",
                DeprecationWarning,
                stacklevel=2
            )
        return self._dual_host.get_client_input()


class GameClient:
    """
    旧版GameClient的兼容性包装器
    
    警告：这是一个兼容性层，建议迁移到DualPlayerClient
    """
    
    def __init__(self):
        warnings.warn(
            "GameClient已弃用，请使用DualPlayerClient。",
            DeprecationWarning,
            stacklevel=2
        )
        
        self._dual_client = DualPlayerClient()
        
        # 兼容性属性
        self.connected = False
        self.player_id = None
        self.player_name = ""
    
    def set_callbacks(self, connection: Callable = None, disconnection: Callable = None,
                     game_state: Callable = None):
        """设置回调函数（兼容性方法）"""
        self._dual_client.set_callbacks(connection, disconnection, game_state)
        
        # 同步状态
        if connection:
            original_callback = connection
            def wrapped_connection(player_id):
                self.connected = True
                self.player_id = player_id
                return original_callback(player_id)
            self._dual_client.connection_callback = wrapped_connection
        
        if disconnection:
            original_callback = disconnection
            def wrapped_disconnection(reason):
                self.connected = False
                self.player_id = None
                return original_callback(reason)
            self._dual_client.disconnection_callback = wrapped_disconnection
    
    def set_tank_selection_callback(self, callback: Callable):
        """设置坦克选择回调函数（兼容性方法）"""
        self._dual_client.set_tank_selection_callback(callback)
    
    def connect_to_host(self, host_ip: str, host_port: int, player_name: str) -> bool:
        """连接到游戏主机（兼容性方法）"""
        result = self._dual_client.connect_to_host(host_ip, host_port, player_name)
        
        # 同步状态
        self.connected = self._dual_client.connected
        self.player_id = self._dual_client.player_id
        self.player_name = self._dual_client.player_name
        
        return result
    
    def disconnect(self):
        """断开连接（兼容性方法）"""
        self._dual_client.disconnect()
        
        # 同步状态
        self.connected = False
        self.player_id = None
        self.player_name = ""
    
    def send_key_press(self, key: str):
        """发送按键按下事件（兼容性方法）"""
        self._dual_client.send_key_press(key)
    
    def send_key_release(self, key: str):
        """发送按键释放事件（兼容性方法）"""
        self._dual_client.send_key_release(key)
    
    def send_message(self, message):
        """发送消息到主机（兼容性方法）"""
        self._dual_client.send_message(message)
    
    def is_connected(self) -> bool:
        """检查是否已连接（兼容性方法）"""
        result = self._dual_client.is_connected()
        self.connected = result  # 同步状态
        return result
    
    def get_player_id(self) -> Optional[str]:
        """获取玩家ID（兼容性方法）"""
        result = self._dual_client.get_player_id()
        self.player_id = result  # 同步状态
        return result
    
    def get_current_keys(self) -> set:
        """获取当前按下的按键（兼容性方法）"""
        return self._dual_client.get_current_keys()


# 兼容性导出
__all__ = ['GameHost', 'GameClient']


def show_migration_warning():
    """显示迁移警告信息"""
    print("=" * 60)
    print("⚠️  双人联机模块兼容性警告")
    print("=" * 60)
    print("您正在使用已弃用的兼容性API。")
    print("建议迁移到新的双人模式API以获得更好的性能：")
    print()
    print("旧版本:")
    print("  from multiplayer import GameHost, GameClient")
    print()
    print("新版本:")
    print("  from multiplayer import DualPlayerHost, DualPlayerClient")
    print()
    print("查看迁移指南: multiplayer/MIGRATION_GUIDE.md")
    print("=" * 60)


# 在模块导入时显示警告
if __name__ != '__main__':
    show_migration_warning()
