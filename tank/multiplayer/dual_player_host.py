"""
双人游戏主机端网络处理

实现简化的双人游戏主机功能，只支持1个主机+1个客户端的连接模式
优化了网络通信，使用点对点发送替代广播，提高效率
"""

import socket
import threading
import time
import uuid
from typing import Optional, Callable, Tuple
from .udp_messages import UDPMessage, MessageType, MessageFactory
from .udp_discovery import RoomAdvertiser


class ClientInfo:
    """客户端信息类 - 双人模式简化版"""

    def __init__(self, client_id: str, address: Tuple[str, int], player_name: str):
        self.client_id = client_id
        self.address = address
        self.player_name = player_name
        self.last_heartbeat = time.time()
        self.connected = True
        
        # 玩家输入状态
        self.current_keys = set()

    def update_heartbeat(self):
        """更新心跳时间"""
        self.last_heartbeat = time.time()

    def is_timeout(self, timeout: float = 3.0) -> bool:
        """检查是否超时"""
        return time.time() - self.last_heartbeat > timeout

    def update_input(self, keys_pressed: list, keys_released: list):
        """更新输入状态"""
        for key in keys_pressed:
            self.current_keys.add(key)
        for key in keys_released:
            self.current_keys.discard(key)


class DualPlayerHost:
    """双人游戏主机类 - 简化版本，只支持1个客户端"""

    def __init__(self, host_port: int = 12346):
        self.host_port = host_port
        self.max_players = 2  # 主机 + 1个客户端

        # 网络相关
        self.host_socket: Optional[socket.socket] = None
        self.running = False
        self.network_thread: Optional[threading.Thread] = None

        # 客户端管理 - 简化为单个客户端
        self.client: Optional[ClientInfo] = None
        self.host_player_id = "host"

        # 房间广播
        self.room_advertiser = RoomAdvertiser()
        self.room_name = ""

        # 回调函数
        self.client_join_callback: Optional[Callable] = None
        self.client_leave_callback: Optional[Callable] = None
        self.input_received_callback: Optional[Callable] = None
        self.tank_selection_callback: Optional[Callable] = None

        # 游戏状态同步 - 优化为点对点
        self.game_state_callback: Optional[Callable] = None
        self.sync_interval = 1.0 / 30.0  # 30Hz
        self.last_sync_time = 0

    def set_callbacks(self, client_join: Callable = None, client_leave: Callable = None,
                     input_received: Callable = None, game_state: Callable = None):
        """设置回调函数"""
        if client_join:
            self.client_join_callback = client_join
        if client_leave:
            self.client_leave_callback = client_leave
        if input_received:
            self.input_received_callback = input_received
        if game_state:
            self.game_state_callback = game_state

    def set_tank_selection_callback(self, callback: Callable):
        """设置坦克选择回调函数"""
        self.tank_selection_callback = callback

    def start_hosting(self, room_name: str) -> bool:
        """开始主机服务"""
        if self.running:
            return False

        self.room_name = room_name

        try:
            # 创建UDP套接字
            self.host_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.host_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.host_socket.bind(('', self.host_port))
            self.host_socket.settimeout(0.1)  # 100ms超时

            self.running = True

            # 启动网络处理线程
            self.network_thread = threading.Thread(target=self._network_loop, daemon=True)
            self.network_thread.start()

            # 开始房间广播 - 显示为等待1个玩家
            self.room_advertiser.start_advertising(
                room_name, self.get_current_player_count(), self.max_players
            )

            print(f"双人游戏主机已启动: {room_name} (端口 {self.host_port})")
            return True

        except Exception as e:
            print(f"启动游戏主机失败: {e}")
            self.stop_hosting()
            return False

    def stop_hosting(self, force=False):
        """停止主机服务"""
        if not self.running or (not force and self.client is not None):
            return False
        
        self.running = False
        
        # 停止房间广播
        self.room_advertiser.stop_advertising()
        
        # 通知客户端断开连接
        if self.host_socket and self.client:
            self._send_to_client(MessageFactory.create_disconnect(
                self.host_player_id, "host_shutdown"
            ))
        
        # 清理网络资源
        if self.host_socket:
            self.host_socket.close()
            self.host_socket = None

        # 清理状态
        self.client = None
        print("双人游戏主机已停止")
        return True

    def get_current_player_count(self) -> int:
        """获取当前玩家数量（主机 + 客户端）"""
        return 1 + (1 if self.client and self.client.connected else 0)

    def is_room_full(self) -> bool:
        """检查房间是否已满（双人模式下只能有1个客户端）"""
        return self.client is not None and self.client.connected

    def get_connected_players(self) -> list:
        """获取所有连接的玩家ID"""
        players = [self.host_player_id]
        if self.client and self.client.connected:
            players.append(self.client.client_id)
        return players

    def send_game_state(self, game_state_data: dict):
        """发送游戏状态给客户端 - 点对点发送"""
        current_time = time.time()
        if current_time - self.last_sync_time < self.sync_interval:
            return

        if not self.client or not self.client.connected:
            return

        message = MessageFactory.create_game_state(
            game_state_data.get("tanks", []),
            game_state_data.get("bullets", []),
            game_state_data.get("round_info", {})
        )

        self._send_to_client(message)
        self.last_sync_time = current_time

    def send_to_client(self, message: UDPMessage):
        """发送消息给客户端"""
        if self.client and self.client.connected:
            self._send_to_client(message)

    def get_client_input(self) -> set:
        """获取客户端当前输入状态"""
        if self.client and self.client.connected:
            return self.client.current_keys.copy()
        return set()

    def get_client_id(self) -> Optional[str]:
        """获取客户端ID"""
        return self.client.client_id if self.client else None

    def _network_loop(self):
        """网络处理主循环 - 双人模式优化"""
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

            # 更新房间广播的玩家数量
            self.room_advertiser.update_player_count(self.get_current_player_count())

    def _handle_client_message(self, data: bytes, addr: Tuple[str, int]):
        """处理客户端消息"""
        try:
            message = UDPMessage.from_bytes(data)

            if message.type == MessageType.JOIN_REQUEST:
                self._handle_join_request(message, addr)

            elif message.type == MessageType.PLAYER_INPUT:
                self._handle_player_input(message, addr)

            elif message.type == MessageType.HEARTBEAT:
                self._handle_heartbeat(message, addr)

            elif message.type == MessageType.PLAYER_DISCONNECT:
                self._handle_disconnect(message, addr)

            # 坦克选择相关消息
            elif message.type in [MessageType.TANK_SELECTED, MessageType.TANK_SELECTION_READY]:
                self._handle_tank_selection_message(message, addr)

        except ValueError:
            # 忽略无效消息
            pass

    def _handle_join_request(self, message: UDPMessage, addr: Tuple[str, int]):
        """处理加入请求 - 双人模式只允许1个客户端"""
        player_name = message.data.get("player_name", "Unknown Player")

        # 检查是否已有客户端连接
        if self.is_room_full():
            response = MessageFactory.create_join_response(
                False, reason="房间已满（双人模式）"
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

        print(f"玩家 {player_name} ({client_id}) 加入双人游戏")

        # 通知游戏逻辑
        if self.client_join_callback:
            self.client_join_callback(client_id, player_name)

    def _handle_player_input(self, message: UDPMessage, addr: Tuple[str, int]):
        """处理玩家输入"""
        if not self.client or message.player_id != self.client.client_id:
            return

        self.client.update_heartbeat()

        # 更新输入状态
        keys_pressed = message.data.get("keys_pressed", [])
        keys_released = message.data.get("keys_released", [])
        self.client.update_input(keys_pressed, keys_released)

        # 通知游戏逻辑
        if self.input_received_callback:
            self.input_received_callback(self.client.client_id, keys_pressed, keys_released)

    def _handle_heartbeat(self, message: UDPMessage, addr: Tuple[str, int]):
        """处理心跳"""
        if self.client and message.player_id == self.client.client_id:
            self.client.update_heartbeat()

    def _handle_disconnect(self, message: UDPMessage, addr: Tuple[str, int]):
        """处理断开连接"""
        if self.client and message.player_id == self.client.client_id:
            self._remove_client("client_disconnect")

    def _handle_tank_selection_message(self, message: UDPMessage, addr: Tuple[str, int]):
        """处理坦克选择相关消息"""
        if not self.client or message.player_id != self.client.client_id:
            return

        # 更新客户端心跳
        self.client.update_heartbeat()

        # 调用坦克选择回调
        if self.tank_selection_callback:
            self.tank_selection_callback(self.client.client_id, message.type, message.data)

    def _check_client_timeout(self):
        """检查客户端超时 - 双人模式简化"""
        if self.client and self.client.connected and self.client.is_timeout():
            self._remove_client("timeout")

    def _remove_client(self, reason: str):
        """移除客户端"""
        if self.client:
            self.client.connected = False
            player_name = self.client.player_name
            client_id = self.client.client_id

            print(f"玩家 {player_name} ({client_id}) 离开双人游戏: {reason}")

            # 通知游戏逻辑
            if self.client_leave_callback:
                self.client_leave_callback(client_id, reason)

            # 清除客户端
            self.client = None

    def _send_to_client(self, message: UDPMessage):
        """发送消息给客户端"""
        if not self.client or not self.client.connected:
            return

        try:
            message_bytes = message.to_bytes()
            self.host_socket.sendto(message_bytes, self.client.address)
        except Exception as e:
            print(f"发送消息给客户端失败: {e}")

    def _send_to_address(self, addr: Tuple[str, int], message: UDPMessage):
        """发送消息到指定地址"""
        try:
            self.host_socket.sendto(message.to_bytes(), addr)
        except Exception as e:
            print(f"发送消息失败: {e}")
