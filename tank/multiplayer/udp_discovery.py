"""
UDP房间发现和广播功能

实现局域网内游戏房间的自动发现和广播机制
"""

import socket
import threading
import time
from typing import Dict, Callable, Optional, Tuple
from .udp_messages import UDPMessage, MessageType, MessageFactory


class RoomInfo:
    """房间信息类"""
    
    def __init__(self, host_ip: str, room_name: str, current_players: int, 
                 max_players: int, game_mode: str = "pvp"):
        self.host_ip = host_ip
        self.room_name = room_name
        self.current_players = current_players
        self.max_players = max_players
        self.game_mode = game_mode
        self.last_seen = time.time()
    
    def is_expired(self, timeout: float = 5.0) -> bool:
        """检查房间信息是否过期"""
        return time.time() - self.last_seen > timeout
    
    def update(self, current_players: int):
        """更新房间信息"""
        self.current_players = current_players
        self.last_seen = time.time()


class RoomDiscovery:
    """房间发现管理器"""
    
    def __init__(self, broadcast_port: int = 12345):
        self.broadcast_port = broadcast_port
        self.rooms: Dict[str, RoomInfo] = {}  # host_ip -> RoomInfo
        self.discovery_socket: Optional[socket.socket] = None
        self.running = False
        self.discovery_thread: Optional[threading.Thread] = None
        self.room_update_callback: Optional[Callable] = None
        
    def set_room_update_callback(self, callback: Callable[[Dict[str, RoomInfo]], None]):
        """设置房间列表更新回调"""
        self.room_update_callback = callback
    
    def start_discovery(self):
        """开始房间发现"""
        if self.running:
            return
            
        try:
            self.discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.discovery_socket.bind(('', self.broadcast_port))
            self.discovery_socket.settimeout(1.0)  # 1秒超时
            
            self.running = True
            self.discovery_thread = threading.Thread(target=self._discovery_loop, daemon=True)
            self.discovery_thread.start()
            
            print(f"房间发现已启动，监听端口 {self.broadcast_port}")
            
        except Exception as e:
            print(f"启动房间发现失败: {e}")
            self.stop_discovery()
    
    def stop_discovery(self):
        """停止房间发现"""
        self.running = False
        
        if self.discovery_socket:
            self.discovery_socket.close()
            self.discovery_socket = None
            
        if self.discovery_thread:
            self.discovery_thread.join(timeout=2.0)
            self.discovery_thread = None
            
        print("房间发现已停止")
    
    def _discovery_loop(self):
        """房间发现主循环"""
        while self.running:
            try:
                # 接收广播消息
                data, addr = self.discovery_socket.recvfrom(1024)
                self._handle_discovery_message(data, addr[0])
                
            except socket.timeout:
                # 超时是正常的，继续循环
                pass
            except Exception as e:
                if self.running:  # 只在运行时报告错误
                    print(f"房间发现错误: {e}")
            
            # 清理过期房间
            self._cleanup_expired_rooms()
    
    def _handle_discovery_message(self, data: bytes, host_ip: str):
        """处理发现消息"""
        try:
            message = UDPMessage.from_bytes(data)
            
            if message.type == MessageType.ROOM_ADVERTISE:
                room_data = message.data
                room_name = room_data.get("room_name", "Unknown Room")
                current_players = room_data.get("current_players", 0)
                max_players = room_data.get("max_players", 4)
                game_mode = room_data.get("game_mode", "pvp")
                
                # 更新或创建房间信息
                if host_ip in self.rooms:
                    self.rooms[host_ip].update(current_players)
                else:
                    self.rooms[host_ip] = RoomInfo(
                        host_ip, room_name, current_players, max_players, game_mode
                    )
                
                # 通知房间列表更新
                if self.room_update_callback:
                    self.room_update_callback(self.get_available_rooms())
                    
        except ValueError as e:
            # 忽略无效消息
            pass
    
    def _cleanup_expired_rooms(self):
        """清理过期房间"""
        expired_rooms = [ip for ip, room in self.rooms.items() if room.is_expired()]
        
        for ip in expired_rooms:
            del self.rooms[ip]
            
        if expired_rooms and self.room_update_callback:
            self.room_update_callback(self.get_available_rooms())
    
    def get_available_rooms(self) -> Dict[str, RoomInfo]:
        """获取可用房间列表"""
        return {ip: room for ip, room in self.rooms.items() 
                if not room.is_expired() and room.current_players < room.max_players}


class RoomAdvertiser:
    """房间广播器"""
    
    def __init__(self, broadcast_port: int = 12345, broadcast_interval: float = 2.0):
        self.broadcast_port = broadcast_port
        self.broadcast_interval = broadcast_interval
        self.broadcast_socket: Optional[socket.socket] = None
        self.running = False
        self.broadcast_thread: Optional[threading.Thread] = None
        
        # 房间信息
        self.room_name = ""
        self.current_players = 0
        self.max_players = 4
        self.game_mode = "pvp"
    
    def start_advertising(self, room_name: str, current_players: int = 1,
                         max_players: int = 2, game_mode: str = "dual_pvp"):
        """开始广播房间"""
        if self.running:
            return
            
        self.room_name = room_name
        self.current_players = current_players
        self.max_players = max_players
        self.game_mode = game_mode
        
        try:
            self.broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
            self.running = True
            self.broadcast_thread = threading.Thread(target=self._broadcast_loop, daemon=True)
            self.broadcast_thread.start()
            
            print(f"开始广播房间: {room_name}")
            
        except Exception as e:
            print(f"启动房间广播失败: {e}")
            self.stop_advertising()
    
    def stop_advertising(self):
        """停止广播房间"""
        self.running = False
        
        if self.broadcast_socket:
            self.broadcast_socket.close()
            self.broadcast_socket = None
            
        if self.broadcast_thread:
            self.broadcast_thread.join(timeout=2.0)
            self.broadcast_thread = None
            
        print("房间广播已停止")
    
    def update_player_count(self, current_players: int):
        """更新玩家数量"""
        self.current_players = current_players
    
    def _broadcast_loop(self):
        """广播主循环"""
        while self.running:
            try:
                # 创建房间广播消息
                message = MessageFactory.create_room_advertise(
                    self.room_name, self.current_players, self.max_players, self.game_mode
                )
                
                # 广播消息
                self.broadcast_socket.sendto(
                    message.to_bytes(), 
                    ('<broadcast>', self.broadcast_port)
                )
                
                # 等待下次广播
                time.sleep(self.broadcast_interval)
                
            except Exception as e:
                if self.running:  # 只在运行时报告错误
                    print(f"房间广播错误: {e}")
                    break
