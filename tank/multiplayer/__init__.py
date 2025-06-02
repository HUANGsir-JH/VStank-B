"""
多人联机游戏模块

这个模块实现了基于UDP的局域网多人游戏功能，包括：
- 房间发现和广播
- 主机-客户端连接管理
- 游戏状态同步
- 输入转发和处理

使用方法：
1. 主机端：创建房间并等待玩家加入
2. 客户端：搜索并加入房间
3. 开始多人游戏
"""

from .udp_discovery import RoomDiscovery
from .udp_host import GameHost
from .udp_client import GameClient
from .udp_messages import MessageType, UDPMessage
from .network_views import NetworkHostView, NetworkClientView, RoomBrowserView

__all__ = [
    'RoomDiscovery',
    'GameHost', 
    'GameClient',
    'MessageType',
    'UDPMessage',
    'NetworkHostView',
    'NetworkClientView', 
    'RoomBrowserView'
]

# 网络配置常量
DISCOVERY_PORT = 12345
GAME_PORT = 12346
BROADCAST_INTERVAL = 2.0  # 房间广播间隔(秒)
GAME_UPDATE_RATE = 30     # 游戏状态更新频率(Hz)
CONNECTION_TIMEOUT = 3.0  # 连接超时时间(秒)
MAX_PLAYERS = 4           # 最大玩家数量
