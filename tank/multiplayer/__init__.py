"""
双人联机游戏模块 - 重构版

这个模块实现了基于UDP的1对1双人游戏功能，包括：
- 简化的房间发现和连接
- 主机-客户端直连架构
- 实时游戏状态同步
- 优化的输入处理

使用方法：
1. 主机端：创建房间并等待1个玩家连接
2. 客户端：搜索并连接到主机
3. 开始双人对战

架构特点：
- 纯1对1连接模式，无多人房间概念
- 主机权威架构，确保游戏状态一致性
- 点对点通信，最小化网络延迟
- 全新API设计，不保留旧版兼容性
"""

from .room_discovery import RoomDiscovery
from .game_host import GameHost
from .game_client import GameClient
from .messages import MessageType, NetworkMessage

# 注意：network_views 需要 arcade，在测试环境中可能不可用
try:
    from .network_views import HostGameView, ClientGameView, RoomBrowserView
    _VIEWS_AVAILABLE = True
except ImportError:
    _VIEWS_AVAILABLE = False
    HostGameView = None
    ClientGameView = None
    RoomBrowserView = None

__all__ = [
    'RoomDiscovery',
    'GameHost',
    'GameClient',
    'MessageType',
    'NetworkMessage'
]

if _VIEWS_AVAILABLE:
    __all__.extend(['HostGameView', 'ClientGameView', 'RoomBrowserView'])

# 网络配置常量 - 1对1游戏优化
DISCOVERY_PORT = 12345
GAME_PORT = 12346
BROADCAST_INTERVAL = 2.0  # 房间广播间隔(秒)
GAME_UPDATE_RATE = 60     # 游戏状态更新频率(Hz) - 提高到60Hz
CONNECTION_TIMEOUT = 5.0  # 连接超时时间(秒)
MAX_PLAYERS = 2           # 固定为2个玩家（主机+客户端）
