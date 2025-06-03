"""
双人游戏客户端网络处理

实现简化的双人游戏客户端功能，优化了与主机的点对点通信
"""

import socket
import threading
import time
from typing import Optional, Callable, Tuple, List, Set
from .udp_messages import UDPMessage, MessageType, MessageFactory


class DualPlayerClient:
    """双人游戏客户端类 - 简化版本"""

    def __init__(self):
        # 网络相关
        self.client_socket: Optional[socket.socket] = None
        self.host_address: Optional[Tuple[str, int]] = None
        self.running = False
        self.network_thread: Optional[threading.Thread] = None
        self.heartbeat_thread: Optional[threading.Thread] = None

        # 客户端状态
        self.player_id: Optional[str] = None
        self.player_name = ""
        self.connected = False

        # 输入状态 - 优化的输入管理
        self.current_keys: Set[str] = set()
        self.pending_key_presses: List[str] = []
        self.pending_key_releases: List[str] = []
        self.input_lock = threading.Lock()

        # 回调函数
        self.connection_callback: Optional[Callable] = None
        self.disconnection_callback: Optional[Callable] = None
        self.game_state_callback: Optional[Callable] = None
        self.tank_selection_callback: Optional[Callable] = None

        # 心跳优化
        self.heartbeat_interval = 1.0  # 1秒发送一次心跳
        self.last_heartbeat_time = 0

    def set_callbacks(self, connection: Callable = None, disconnection: Callable = None,
                     game_state: Callable = None):
        """设置回调函数"""
        if connection:
            self.connection_callback = connection
        if disconnection:
            self.disconnection_callback = disconnection
        if game_state:
            self.game_state_callback = game_state

    def set_tank_selection_callback(self, callback: Callable):
        """设置坦克选择回调函数"""
        self.tank_selection_callback = callback

    def connect_to_host(self, host_ip: str, host_port: int, player_name: str) -> bool:
        """连接到双人游戏主机"""
        if self.connected:
            return False

        self.player_name = player_name
        self.host_address = (host_ip, host_port)

        try:
            # 创建UDP套接字
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.client_socket.settimeout(5.0)  # 5秒连接超时

            # 发送加入请求
            join_request = MessageFactory.create_join_request(player_name)
            self.client_socket.sendto(join_request.to_bytes(), self.host_address)

            # 等待响应
            data, addr = self.client_socket.recvfrom(8192)
            response = UDPMessage.from_bytes(data)

            if response.type == MessageType.JOIN_RESPONSE and response.data.get("success"):
                self.player_id = response.data.get("player_id")
                self.connected = True

                # 设置非阻塞模式
                self.client_socket.settimeout(0.1)

                # 启动网络线程
                self.running = True
                self.network_thread = threading.Thread(target=self._network_loop, daemon=True)
                self.network_thread.start()

                # 启动心跳线程
                self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
                self.heartbeat_thread.start()

                print(f"成功连接到双人游戏主机 {host_ip}:{host_port} (玩家ID: {self.player_id})")

                # 通知连接成功
                if self.connection_callback:
                    self.connection_callback(self.player_id)

                # 延迟初始化，等待服务器确认连接
                threading.Timer(0.5, self._delayed_initialization).start()
                
                return True
            else:
                reason = response.data.get("reason", "未知错误")
                print(f"连接被拒绝: {reason}")
                self.disconnect()
                return False

        except Exception as e:
            print(f"连接双人游戏主机失败: {e}")
            self.disconnect()
            return False

    def _delayed_initialization(self):
        """延迟初始化游戏视图，确保连接完全建立"""
        # 请求坦克选择状态同步
        sync_request = MessageFactory.create_tank_selection_sync_request()
        self.send_message(sync_request)

    def disconnect(self):
        """断开连接"""
        if not self.connected:
            return

        # 发送断开连接消息
        if self.client_socket and self.host_address and self.player_id:
            try:
                disconnect_msg = MessageFactory.create_disconnect(self.player_id)
                self.client_socket.sendto(disconnect_msg.to_bytes(), self.host_address)
            except:
                pass

        # 停止网络处理
        self.running = False
        self.connected = False

        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None

        # 等待线程结束
        if self.network_thread:
            self.network_thread.join(timeout=2.0)
            self.network_thread = None

        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=2.0)
            self.heartbeat_thread = None

        # 清理状态
        self.player_id = None
        self.host_address = None
        with self.input_lock:
            self.current_keys.clear()
            self.pending_key_presses.clear()
            self.pending_key_releases.clear()

        print("已断开双人游戏连接")

        # 通知断开连接
        if self.disconnection_callback:
            self.disconnection_callback("user_disconnect")

    def send_key_press(self, key: str):
        """发送按键按下事件 - 优化的输入处理"""
        if not self.connected:
            return

        with self.input_lock:
            if key not in self.current_keys:
                self.current_keys.add(key)
                self.pending_key_presses.append(key)

    def send_key_release(self, key: str):
        """发送按键释放事件 - 优化的输入处理"""
        if not self.connected:
            return

        with self.input_lock:
            if key in self.current_keys:
                self.current_keys.remove(key)
                self.pending_key_releases.append(key)

    def send_message(self, message: UDPMessage):
        """发送消息到主机"""
        if not self.connected or not self.client_socket:
            return

        try:
            self.client_socket.sendto(message.to_bytes(), self.host_address)
        except Exception as e:
            print(f"发送消息失败: {e}")

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
        """网络处理主循环 - 双人模式优化"""
        while self.running and self.connected:
            try:
                # 发送待处理的输入
                self._send_pending_input()

                # 接收消息
                try:
                    data, addr = self.client_socket.recvfrom(8192)
                    self._handle_server_message(data)
                except socket.timeout:
                    # 超时是正常的，继续循环
                    pass

            except Exception as e:
                if self.running:
                    print(f"网络处理错误: {e}")
                    self._handle_connection_lost("network_error")
                    break

    def _send_pending_input(self):
        """发送待处理的输入 - 优化的批量发送"""
        with self.input_lock:
            if self.pending_key_presses or self.pending_key_releases:
                input_msg = MessageFactory.create_player_input(
                    self.player_id,
                    self.pending_key_presses.copy(),
                    self.pending_key_releases.copy()
                )

                try:
                    self.client_socket.sendto(input_msg.to_bytes(), self.host_address)
                    self.pending_key_presses.clear()
                    self.pending_key_releases.clear()
                except Exception as e:
                    print(f"发送输入失败: {e}")

    def _handle_server_message(self, data: bytes):
        """处理服务器消息 - 双人模式优化"""
        try:
            message = UDPMessage.from_bytes(data)

            if message.type == MessageType.GAME_STATE:
                # 处理游戏状态更新
                if self.game_state_callback:
                    self.game_state_callback(message.data)

            elif message.type == MessageType.PLAYER_DISCONNECT:
                # 服务器通知断开连接
                reason = message.data.get("reason", "server_disconnect")
                self._handle_connection_lost(reason)

            # 坦克选择相关消息
            elif message.type in [MessageType.TANK_SELECTION_SYNC, MessageType.TANK_SELECTION_CONFLICT]:
                if self.tank_selection_callback:
                    self.tank_selection_callback(message.type, message.data)

        except ValueError:
            # 忽略无效消息
            pass

    def _heartbeat_loop(self):
        """心跳发送循环 - 双人模式优化"""
        while self.running and self.connected:
            try:
                current_time = time.time()
                if current_time - self.last_heartbeat_time >= self.heartbeat_interval:
                    heartbeat_msg = MessageFactory.create_heartbeat(self.player_id)
                    self.client_socket.sendto(heartbeat_msg.to_bytes(), self.host_address)
                    self.last_heartbeat_time = current_time

                time.sleep(0.1)  # 100ms检查间隔

            except Exception as e:
                if self.running:
                    print(f"心跳发送错误: {e}")
                    break

    def _handle_connection_lost(self, reason: str):
        """处理连接丢失 - 双人模式优化"""
        if self.connected:
            self.connected = False
            print(f"双人游戏连接丢失: {reason}")

            # 通知断开连接
            if self.disconnection_callback:
                self.disconnection_callback(reason)

            # 清理输入状态
            with self.input_lock:
                self.current_keys.clear()
                self.pending_key_presses.clear()
                self.pending_key_releases.clear()
