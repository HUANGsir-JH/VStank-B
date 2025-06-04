"""
游戏客户端类 - 重构版

专为1对1双人游戏设计的客户端网络管理
"""

import socket
import threading
import time
from typing import Optional, Callable, Set, Tuple
from .messages import MessageFactory, NetworkMessage, MessageType


class GameClient:
    """游戏客户端类 - 重构版"""
    
    def __init__(self):
        self.connected = False
        self.running = False
        
        # 网络相关
        self.client_socket = None
        self.network_thread = None
        self.host_address: Optional[Tuple[str, int]] = None
        
        # 玩家信息
        self.player_id: Optional[str] = None
        self.player_name = ""
        
        # 输入管理
        self.current_keys: Set[str] = set()
        self.pending_key_presses = []
        self.pending_key_releases = []
        self.input_lock = threading.Lock()
        
        # 回调函数
        self.connection_callback: Optional[Callable[[str], None]] = None
        self.disconnection_callback: Optional[Callable[[str], None]] = None
        self.game_state_callback: Optional[Callable[[dict], None]] = None
        self.game_start_callback: Optional[Callable[[dict], None]] = None
        self.game_end_callback: Optional[Callable[[dict], None]] = None
        self.tank_selection_callback: Optional[Callable] = None
        self.map_sync_callback: Optional[Callable[[dict], None]] = None
        
        # 心跳管理
        self.last_heartbeat = 0
        self.heartbeat_interval = 5.0  # 5秒发送一次心跳
    
    def set_callbacks(self, connection: Callable = None, disconnection: Callable = None,
                     game_state: Callable = None, game_start: Callable = None, game_end: Callable = None,
                     tank_selection: Callable = None, map_sync: Callable = None):
        """设置回调函数"""
        self.connection_callback = connection
        self.disconnection_callback = disconnection
        self.game_state_callback = game_state
        self.game_start_callback = game_start
        self.game_end_callback = game_end
        self.tank_selection_callback = tank_selection
        self.map_sync_callback = map_sync
    
    def connect_to_host(self, host_ip: str, host_port: int, player_name: str) -> bool:
        """连接到游戏主机"""
        if self.connected:
            return False
        
        self.host_address = (host_ip, host_port)
        self.player_name = player_name
        
        try:
            # 创建UDP套接字
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.client_socket.settimeout(5.0)  # 5秒连接超时
            
            # 发送加入请求
            join_request = MessageFactory.create_join_request(player_name)
            self.client_socket.sendto(join_request.to_bytes(), self.host_address)
            
            # 等待响应
            data, addr = self.client_socket.recvfrom(8192)
            response = NetworkMessage.from_bytes(data)
            
            if response.type == MessageType.JOIN_RESPONSE and response.data.get("success"):
                # 连接成功
                self.player_id = response.data.get("player_id")
                self.connected = True
                self.running = True
                
                # 设置非阻塞模式
                self.client_socket.settimeout(0.1)
                
                # 启动网络处理线程
                self.network_thread = threading.Thread(target=self._network_loop, daemon=True)
                self.network_thread.start()
                
                print(f"成功连接到主机: {host_ip}:{host_port}")
                
                # 通知连接成功
                if self.connection_callback:
                    self.connection_callback(self.player_id)
                
                return True
            else:
                reason = response.data.get("reason", "未知错误")
                print(f"连接被拒绝: {reason}")
                self.disconnect()
                return False
                
        except Exception as e:
            print(f"连接主机失败: {e}")
            self.disconnect()
            return False
    
    def disconnect(self):
        """断开连接"""
        if not self.connected:
            return
        
        # 发送断开连接消息
        if self.client_socket and self.host_address:
            try:
                disconnect_msg = MessageFactory.create_disconnect("用户断开")
                self.client_socket.sendto(disconnect_msg.to_bytes(), self.host_address)
            except:
                pass
        
        # 停止网络处理
        self.running = False
        self.connected = False
        
        # 关闭套接字
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None
        
        # 等待网络线程结束
        if self.network_thread:
            self.network_thread.join(timeout=1.0)
            self.network_thread = None
        
        # 清理状态
        self.player_id = None
        self.host_address = None
        with self.input_lock:
            self.current_keys.clear()
            self.pending_key_presses.clear()
            self.pending_key_releases.clear()
        
        print("已断开连接")
        
        # 通知断开连接
        if self.disconnection_callback:
            self.disconnection_callback("用户断开")
    
    def send_key_press(self, key: str):
        """发送按键按下事件"""
        if not self.connected:
            return
        
        with self.input_lock:
            if key not in self.current_keys:
                self.current_keys.add(key)
                self.pending_key_presses.append(key)
    
    def send_key_release(self, key: str):
        """发送按键释放事件"""
        if not self.connected:
            return
        
        with self.input_lock:
            if key in self.current_keys:
                self.current_keys.remove(key)
                self.pending_key_releases.append(key)
    
    def send_message(self, message: NetworkMessage):
        """发送消息到主机"""
        if not self.connected or not self.client_socket:
            return
        
        try:
            self.client_socket.sendto(message.to_bytes(), self.host_address)
        except Exception as e:
            print(f"发送消息失败: {e}")
    
    def send_tank_selection(self, tank_type: str, tank_image: str):
        """发送坦克选择"""
        message = MessageFactory.create_tank_selected(tank_type, tank_image)
        self.send_message(message)
    
    def send_tank_selection_ready(self):
        """发送坦克选择完成"""
        message = MessageFactory.create_tank_selection_ready()
        self.send_message(message)
    
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self.connected
    
    def get_player_id(self) -> Optional[str]:
        """获取玩家ID"""
        return self.player_id
    
    def get_current_keys(self) -> Set[str]:
        """获取当前按下的按键"""
        with self.input_lock:
            return self.current_keys.copy()
    
    def _network_loop(self):
        """网络处理主循环"""
        while self.running and self.connected:
            try:
                # 发送待处理的输入
                self._send_pending_input()
                
                # 发送心跳包
                self._send_heartbeat_if_needed()
                
                # 接收消息
                try:
                    data, addr = self.client_socket.recvfrom(8192)
                    self._handle_server_message(data)
                except socket.timeout:
                    # 超时是正常的，继续循环
                    pass
                
            except Exception as e:
                if self.running:
                    # 检查是否是连接被强制关闭的错误
                    if "10054" in str(e) or "远程主机强迫关闭" in str(e):
                        print(f"连接被远程主机关闭: {e}")
                        self._handle_connection_lost("远程主机关闭连接")
                    else:
                        print(f"网络处理错误: {e}")
                        self._handle_connection_lost("网络错误")
                    break
    
    def _send_pending_input(self):
        """发送待处理的输入"""
        with self.input_lock:
            if self.pending_key_presses or self.pending_key_releases:
                message = MessageFactory.create_player_input(
                    self.pending_key_presses.copy(),
                    self.pending_key_releases.copy()
                )
                
                # 清空待处理列表
                self.pending_key_presses.clear()
                self.pending_key_releases.clear()
                
                # 发送消息
                try:
                    self.client_socket.sendto(message.to_bytes(), self.host_address)
                except Exception as e:
                    print(f"发送输入失败: {e}")
    
    def _send_heartbeat_if_needed(self):
        """根据需要发送心跳包"""
        current_time = time.time()
        if current_time - self.last_heartbeat > self.heartbeat_interval:
            try:
                heartbeat = MessageFactory.create_heartbeat()
                self.client_socket.sendto(heartbeat.to_bytes(), self.host_address)
                self.last_heartbeat = current_time
            except Exception as e:
                print(f"发送心跳失败: {e}")
    
    def _handle_server_message(self, data: bytes):
        """处理服务器消息"""
        try:
            message = NetworkMessage.from_bytes(data)

            if message.type == MessageType.GAME_STATE:
                self._handle_game_state(message)
            elif message.type == MessageType.GAME_START:
                self._handle_game_start(message)
            elif message.type == MessageType.MAP_SYNC:
                self._handle_map_sync(message)
            elif message.type == MessageType.DISCONNECT:
                self._handle_server_disconnect(message)
            elif message.type == MessageType.TANK_SELECTION_START:
                self._handle_tank_selection_start(message)
            elif message.type == MessageType.TANK_SELECTION_SYNC:
                self._handle_tank_selection_sync(message)
            elif message.type == MessageType.GAME_END:
                self._handle_game_end(message)

        except Exception as e:
            # 检查是否是OpenGL错误
            if "OpenGL" in str(e) or "1282" in str(e) or "Invalid operation" in str(e):
                print(f"OpenGL操作错误（可能在错误线程中执行）: {e}")
                # 不要因为OpenGL错误而断开连接，这通常是线程问题
            else:
                print(f"处理服务器消息失败: {e}")
    
    def _handle_game_state(self, message: NetworkMessage):
        """处理游戏状态更新"""
        if self.game_state_callback:
            try:
                self.game_state_callback(message.data)
            except Exception as e:
                # 检查是否是OpenGL错误
                if "OpenGL" in str(e) or "1282" in str(e) or "Invalid operation" in str(e):
                    print(f"游戏状态回调中的OpenGL错误（线程安全问题）: {e}")
                    # 不要重新抛出OpenGL错误，这会导致网络线程崩溃
                else:
                    print(f"游戏状态回调失败: {e}")
                    # 对于非OpenGL错误，可以考虑重新抛出

    def _handle_game_start(self, message: NetworkMessage):
        """处理游戏开始消息"""
        if self.game_start_callback:
            try:
                self.game_start_callback(message.data)
            except Exception as e:
                # 检查是否是OpenGL错误
                if "OpenGL" in str(e) or "1282" in str(e) or "Invalid operation" in str(e):
                    print(f"游戏开始回调中的OpenGL错误（线程安全问题）: {e}")
                else:
                    print(f"游戏开始回调失败: {e}")
    
    def _handle_server_disconnect(self, message: NetworkMessage):
        """处理服务器断开连接"""
        reason = message.data.get("reason", "服务器断开")
        self._handle_connection_lost(reason)
    
    def _handle_tank_selection_start(self, message: NetworkMessage):
        """处理坦克选择开始"""
        if self.tank_selection_callback:
            self.tank_selection_callback("start", message.data)
    
    def _handle_tank_selection_sync(self, message: NetworkMessage):
        """处理坦克选择同步"""
        if self.tank_selection_callback:
            self.tank_selection_callback("sync", message.data)

    def _handle_game_end(self, message: NetworkMessage):
        """处理游戏结束消息"""
        if self.game_end_callback:
            try:
                self.game_end_callback(message.data)
            except Exception as e:
                # 检查是否是OpenGL错误
                if "OpenGL" in str(e) or "1282" in str(e) or "Invalid operation" in str(e):
                    print(f"游戏结束回调中的OpenGL错误（线程安全问题）: {e}")
                else:
                    print(f"游戏结束回调失败: {e}")

    def _handle_map_sync(self, message: NetworkMessage):
        """处理地图同步消息"""
        if self.map_sync_callback:
            try:
                self.map_sync_callback(message.data)
            except Exception as e:
                # 检查是否是OpenGL错误
                if "OpenGL" in str(e) or "1282" in str(e) or "Invalid operation" in str(e):
                    print(f"地图同步回调中的OpenGL错误（线程安全问题）: {e}")
                else:
                    print(f"地图同步回调失败: {e}")
    
    def _handle_connection_lost(self, reason: str):
        """处理连接丢失"""
        if not self.connected:
            return

        print(f"连接丢失: {reason}")

        # 清理连接状态
        self.connected = False
        self.running = False

        # 安全地通知断开连接
        try:
            if self.disconnection_callback:
                self.disconnection_callback(reason)
        except Exception as e:
            print(f"断开连接回调执行失败: {e}")
