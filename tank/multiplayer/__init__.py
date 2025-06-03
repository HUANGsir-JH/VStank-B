"""
双人联机游戏模块

这个模块实现了基于UDP的局域网双人游戏功能，包括：
- 房间发现和广播
- 主机-客户端连接管理（1对1）
- 游戏状态同步
- 输入转发和处理

使用方法：
1. 主机端：创建房间并等待1个玩家加入
2. 客户端：搜索并加入房间
3. 开始双人游戏

架构特点：
- 简化的双人模式，只支持1个主机+1个客户端
- 主机权威模式，确保游戏状态一致性
- 优化的点对点通信，减少网络开销
"""

from .udp_discovery import RoomDiscovery
from .dual_player_host import DualPlayerHost
from .dual_player_client import DualPlayerClient
from .udp_messages import MessageType, UDPMessage

# 注意：network_views 需要 arcade，在测试环境中可能不可用
try:
    from .network_views import NetworkHostView, NetworkClientView, RoomBrowserView
    _VIEWS_AVAILABLE = True
except ImportError:
    _VIEWS_AVAILABLE = False
    NetworkHostView = None
    NetworkClientView = None
    RoomBrowserView = None

# 兼容性支持：提供旧版API的访问
try:
    from .compatibility import GameHost, GameClient
    _COMPATIBILITY_AVAILABLE = True
except ImportError:
    _COMPATIBILITY_AVAILABLE = False
    GameHost = None
    GameClient = None

__all__ = [
    'RoomDiscovery',
    'DualPlayerHost',
    'DualPlayerClient',
    'MessageType',
    'UDPMessage'
]

if _VIEWS_AVAILABLE:
    __all__.extend(['NetworkHostView', 'NetworkClientView', 'RoomBrowserView'])

if _COMPATIBILITY_AVAILABLE:
    __all__.extend(['GameHost', 'GameClient'])

# 网络配置常量 - 双人游戏优化
DISCOVERY_PORT = 12345
GAME_PORT = 12346
BROADCAST_INTERVAL = 2.0  # 房间广播间隔(秒)
GAME_UPDATE_RATE = 30     # 游戏状态更新频率(Hz)
CONNECTION_TIMEOUT = 3.0  # 连接超时时间(秒)
MAX_PLAYERS = 2           # 最大玩家数量（主机+1个客户端）
