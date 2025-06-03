"""
游戏主机类 - 重构版

专为1对1双人游戏设计的主机端网络管理
"""

import socket
import threading
import time
import uuid
from typing import Optional, Callable, Dict, Any, Set
from .messages import MessageFactory, NetworkMessage, MessageType
from .room_discovery import RoomDiscovery


class ClientInfo:
    """客户端信息类"""
    
    def __init__(self, client_id: str, address: tuple, player_name: str):
        self.client_id = client_id
        self.address = address
        self.player_name = player_name
        self.last_heartbeat = time.time()
        self.current_keys: Set[str] = set()
    
    def update_heartbeat(self):
        """更新心跳时间"""
        self.last_heartbeat = time.time()
    
    def is_timeout(self, timeout: float = 10.0) -> bool:
        """检查是否超时"""
        return time.time() - self.last_heartbeat > timeout


class GameHost:
    """游戏主机类 - 重构版"""
    
    def __init__(self, host_port: int = 12346):
        self.host_port = host_port
        self.running = False
        
        # 网络相关
        self.host_socket = None
        self.network_thread = None
        
        # 房间发现
        self.room_discovery = RoomDiscovery(host_port - 1)  # 发现端口 = 游戏端口 - 1
        self.room_name = ""
        
        # 客户端管理（1对1模式，只有一个客户端）
        self.client: Optional[ClientInfo] = None
        
        # 回调函数
        self.client_join_callback: Optional[Callable[[str, str], None]] = None
        self.client_leave_callback: Optional[Callable[[str, str], None]] = None
        self.input_received_callback: Optional[Callable[[str, list, list], None]] = None
        self.tank_selection_callback: Optional[Callable] = None
    
    def set_callbacks(self, client_join: Callable = None, client_leave: Callable = None,
                     input_received: Callable = None, tank_selection: Callable = None):
        """设置回调函数"""
        self.client_join_callback = client_join
        self.client_leave_callback = client_leave
        self.input_received_callback = input_received
        self.tank_selection_callback = tank_selection
    
    def start_hosting(self, room_name: str, host_name: str = "主机") -> bool:
        """开始主机服务"""
        if self.running:
            return False
        
        self.room_name = room_name
        
        try:
            # 创建UDP套接字
            self.host_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.host_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.host_socket.bind(('', self.host_port))
            self.host_socket.settimeout(0.1)
            
            self.running = True
            
            # 启动网络处理线程
            self.network_thread = threading.Thread(target=self._network_loop, daemon=True)
            self.network_thread.start()
            
            # 开始房间广播
            self.room_discovery.start_advertising(room_name, host_name)
            
            print(f"游戏主机已启动: {room_name} (端口 {self.host_port})")
            return True
            
        except Exception as e:
            print(f"启动游戏主机失败: {e}")
            self.stop_hosting()
            return False
    
    def stop_hosting(self, force: bool = False):
        """停止主机服务"""
        self.running = False
        
        # 通知客户端断开连接
        if self.client and not force:
            disconnect_msg = MessageFactory.create_disconnect("主机关闭")
            self._send_to_client(disconnect_msg)
        
        # 停止房间广播
        self.room_discovery.stop_advertising()
        
        # 关闭网络套接字
        if self.host_socket:
            try:
                self.host_socket.close()
            except:
                pass
            self.host_socket = None
        
        # 等待网络线程结束
        if self.network_thread:
            self.network_thread.join(timeout=1.0)
            self.network_thread = None
        
        # 清理客户端信息
        if self.client and self.client_leave_callback:
            self.client_leave_callback(self.client.client_id, "主机关闭")
        self.client = None
        
        print("游戏主机已停止")
    
    def get_current_player_count(self) -> int:
        """获取当前玩家数量"""
        return 1 + (1 if self.client else 0)  # 主机 + 客户端
    
    def is_room_full(self) -> bool:
        """检查房间是否已满"""
        return self.client is not None
    
    def get_connected_players(self) -> list:
        """获取连接的玩家列表"""
        players = ["host"]  # 主机自己
        if self.client:
            players.append(self.client.client_id)
        return players
    
    def send_game_state(self, game_state: Dict[str, Any]):
        """发送游戏状态给客户端"""
        if not self.client:
            return
        
        message = MessageFactory.create_game_state(
            tanks=game_state.get("tanks", []),
            bullets=game_state.get("bullets", []),
            scores=game_state.get("scores", {})
        )
        self._send_to_client(message)
    
    def send_to_client(self, message: NetworkMessage):
        """发送消息给客户端"""
        self._send_to_client(message)
    
    def get_client_input(self) -> Set[str]:
        """获取客户端当前输入状态"""
        if self.client:
            return self.client.current_keys.copy()
        return set()
    
    def broadcast_tank_selection_start(self):
        """广播坦克选择开始"""
        if self.client:
            message = MessageFactory.create_tank_selection_start()
            self._send_to_client(message)
    
    def _network_loop(self):
        """网络处理主循环"""
        while self.running:
            try:
                # 接收消息
                data, addr = self.host_socket.recvfrom(8192)
                self._handle_client_message(data, addr)
                
            except socket.timeout:
                # 超时是正常的，继续循环
                pass
            except Exception as e:
                if self.running:
                    print(f"网络处理错误: {e}")
            
            # 检查客户端超时
            self._check_client_timeout()
    
    def _handle_client_message(self, data: bytes, addr: tuple):
        """处理客户端消息"""
        try:
            message = NetworkMessage.from_bytes(data)
            
            if message.type == MessageType.JOIN_REQUEST:
                self._handle_join_request(message, addr)
            elif message.type == MessageType.PLAYER_INPUT:
                self._handle_player_input(message)
            elif message.type == MessageType.HEARTBEAT:
                self._handle_heartbeat(message)
            elif message.type == MessageType.DISCONNECT:
                self._handle_client_disconnect(message)
            elif message.type == MessageType.TANK_SELECTED:
                self._handle_tank_selection(message)
            
        except Exception as e:
            print(f"处理客户端消息失败: {e}")
    
    def _handle_join_request(self, message: NetworkMessage, addr: tuple):
        """处理加入请求"""
        player_name = message.data.get("player_name", "未知玩家")
        
        # 检查是否已满员
        if self.is_room_full():
            response = MessageFactory.create_join_response(
                False, reason="房间已满"
            )
            self._send_to_address(addr, response)
            return
        
        # 生成客户端ID
        client_id = f"client_{uuid.uuid4().hex[:8]}"
        
        # 创建客户端信息
        self.client = ClientInfo(client_id, addr, player_name)
        
        # 发送成功响应
        response = MessageFactory.create_join_response(True, client_id)
        self._send_to_address(addr, response)
        
        print(f"玩家 {player_name} ({client_id}) 加入游戏")
        
        # 通知游戏逻辑
        if self.client_join_callback:
            self.client_join_callback(client_id, player_name)
    
    def _handle_player_input(self, message: NetworkMessage):
        """处理玩家输入"""
        if not self.client:
            return
        
        # 更新客户端心跳
        self.client.update_heartbeat()
        
        # 处理输入
        keys_pressed = message.data.get("keys_pressed", [])
        keys_released = message.data.get("keys_released", [])
        
        # 更新当前按键状态
        for key in keys_pressed:
            self.client.current_keys.add(key)
        for key in keys_released:
            self.client.current_keys.discard(key)
        
        # 通知游戏逻辑
        if self.input_received_callback:
            self.input_received_callback(self.client.client_id, keys_pressed, keys_released)
    
    def _handle_heartbeat(self, message: NetworkMessage):
        """处理心跳包"""
        if self.client:
            self.client.update_heartbeat()
    
    def _handle_client_disconnect(self, message: NetworkMessage):
        """处理客户端断开连接"""
        if self.client:
            reason = message.data.get("reason", "客户端断开")
            client_id = self.client.client_id
            
            # 清理客户端
            self.client = None
            
            print(f"客户端 {client_id} 断开连接: {reason}")
            
            # 通知游戏逻辑
            if self.client_leave_callback:
                self.client_leave_callback(client_id, reason)
    
    def _handle_tank_selection(self, message: NetworkMessage):
        """处理坦克选择"""
        if self.tank_selection_callback:
            self.tank_selection_callback(message)
    
    def _check_client_timeout(self):
        """检查客户端超时"""
        if self.client and self.client.is_timeout():
            print(f"客户端 {self.client.client_id} 超时断开")
            
            client_id = self.client.client_id
            self.client = None
            
            if self.client_leave_callback:
                self.client_leave_callback(client_id, "超时")
    
    def _send_to_client(self, message: NetworkMessage):
        """发送消息给客户端"""
        if self.client:
            self._send_to_address(self.client.address, message)
    
    def _send_to_address(self, addr: tuple, message: NetworkMessage):
        """发送消息到指定地址"""
        try:
            self.host_socket.sendto(message.to_bytes(), addr)
        except Exception as e:
            print(f"发送消息失败: {e}")
