"""
房间发现模块 - 重构版

专为1对1双人游戏设计的简化房间发现机制
"""

import socket
import threading
import time
from typing import Dict, List, Callable, Optional, Tuple
from .messages import MessageFactory, NetworkMessage, MessageType


class RoomInfo:
    """房间信息类"""
    
    def __init__(self, room_name: str, host_name: str, host_ip: str, host_port: int):
        self.room_name = room_name
        self.host_name = host_name
        self.host_ip = host_ip
        self.host_port = host_port
        self.last_seen = time.time()
        self.players = 1  # 主机自己
        self.max_players = 2
        self.game_mode = "1v1"
    
    def is_expired(self, timeout: float = 10.0) -> bool:
        """检查房间信息是否过期"""
        return time.time() - self.last_seen > timeout
    
    def update_last_seen(self):
        """更新最后看到的时间"""
        self.last_seen = time.time()
    
    def __str__(self):
        return f"{self.room_name} ({self.host_name}) - {self.players}/{self.max_players}"


class RoomDiscovery:
    """房间发现类 - 重构版"""
    
    def __init__(self, discovery_port: int = 12345):
        self.discovery_port = discovery_port
        self.running = False
        
        # 房间广播相关
        self.broadcast_socket = None
        self.broadcast_thread = None
        self.room_name = ""
        self.host_name = ""
        
        # 房间搜索相关
        self.listen_socket = None
        self.listen_thread = None
        self.discovered_rooms: Dict[str, RoomInfo] = {}
        self.room_update_callback: Optional[Callable[[List[RoomInfo]], None]] = None
        
        # 线程安全
        self.rooms_lock = threading.Lock()
    
    def start_advertising(self, room_name: str, host_name: str = "主机"):
        """开始广播房间"""
        if self.running:
            return False
        
        self.room_name = room_name
        self.host_name = host_name
        
        try:
            # 创建广播套接字
            self.broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
            self.running = True
            self.broadcast_thread = threading.Thread(target=self._broadcast_loop, daemon=True)
            self.broadcast_thread.start()
            
            print(f"开始广播房间: {room_name}")
            return True
            
        except Exception as e:
            print(f"启动房间广播失败: {e}")
            self.stop_advertising()
            return False
    
    def stop_advertising(self):
        """停止广播房间"""
        self.running = False
        
        if self.broadcast_socket:
            try:
                self.broadcast_socket.close()
            except:
                pass
            self.broadcast_socket = None
        
        if self.broadcast_thread:
            self.broadcast_thread.join(timeout=1.0)
            self.broadcast_thread = None
        
        print("房间广播已停止")
    
    def start_discovery(self, room_update_callback: Callable[[List[RoomInfo]], None] = None):
        """开始搜索房间"""
        if self.running:
            return False
        
        self.room_update_callback = room_update_callback
        
        try:
            # 创建监听套接字
            self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.listen_socket.bind(('', self.discovery_port))
            self.listen_socket.settimeout(1.0)
            
            self.running = True
            self.listen_thread = threading.Thread(target=self._discovery_loop, daemon=True)
            self.listen_thread.start()
            
            print("开始搜索房间...")
            return True
            
        except Exception as e:
            print(f"启动房间搜索失败: {e}")
            self.stop_discovery()
            return False
    
    def stop_discovery(self):
        """停止搜索房间"""
        self.running = False
        
        if self.listen_socket:
            try:
                self.listen_socket.close()
            except:
                pass
            self.listen_socket = None
        
        if self.listen_thread:
            self.listen_thread.join(timeout=1.0)
            self.listen_thread = None
        
        with self.rooms_lock:
            self.discovered_rooms.clear()
        
        print("房间搜索已停止")
    
    def get_discovered_rooms(self) -> List[RoomInfo]:
        """获取发现的房间列表"""
        with self.rooms_lock:
            # 清理过期房间
            current_time = time.time()
            expired_keys = [
                key for key, room in self.discovered_rooms.items()
                if room.is_expired()
            ]
            for key in expired_keys:
                del self.discovered_rooms[key]
            
            return list(self.discovered_rooms.values())
    
    def _broadcast_loop(self):
        """房间广播循环"""
        while self.running:
            try:
                # 创建房间广播消息
                message = MessageFactory.create_room_advertise(self.room_name, self.host_name)
                
                # 广播到局域网
                self.broadcast_socket.sendto(
                    message.to_bytes(),
                    ('<broadcast>', self.discovery_port)
                )
                
                # 等待下次广播
                time.sleep(2.0)  # 每2秒广播一次
                
            except Exception as e:
                if self.running:
                    print(f"房间广播错误: {e}")
                break
    
    def _discovery_loop(self):
        """房间发现循环"""
        while self.running:
            try:
                # 接收广播消息
                data, addr = self.listen_socket.recvfrom(1024)
                self._handle_room_advertise(data, addr)
                
            except socket.timeout:
                # 超时是正常的，继续循环
                pass
            except Exception as e:
                if self.running:
                    print(f"房间发现错误: {e}")
                break
            
            # 定期清理过期房间并通知更新
            self._cleanup_and_notify()
    
    def _handle_room_advertise(self, data: bytes, addr: Tuple[str, int]):
        """处理房间广播消息"""
        try:
            message = NetworkMessage.from_bytes(data)
            
            if message.type != MessageType.ROOM_ADVERTISE:
                return
            
            # 提取房间信息
            room_data = message.data
            room_name = room_data.get("room_name", "未知房间")
            host_name = room_data.get("host_name", "未知主机")
            host_ip = addr[0]
            
            # 假设游戏端口是发现端口+1
            host_port = self.discovery_port + 1
            
            # 创建房间信息
            room_key = f"{host_ip}:{host_port}"
            
            with self.rooms_lock:
                if room_key in self.discovered_rooms:
                    # 更新现有房间
                    self.discovered_rooms[room_key].update_last_seen()
                else:
                    # 添加新房间
                    room_info = RoomInfo(room_name, host_name, host_ip, host_port)
                    self.discovered_rooms[room_key] = room_info
                    print(f"发现新房间: {room_info}")
            
        except Exception as e:
            print(f"处理房间广播失败: {e}")
    
    def _cleanup_and_notify(self):
        """清理过期房间并通知更新"""
        rooms = self.get_discovered_rooms()
        
        if self.room_update_callback:
            try:
                self.room_update_callback(rooms)
            except Exception as e:
                print(f"房间更新回调错误: {e}")
