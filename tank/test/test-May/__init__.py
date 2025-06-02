"""
测试包

包含所有测试相关的文件和工具
"""

# 测试包版本
__version__ = "1.0.0"

# 导入主要测试模块
from .test_multiplayer import *
from .test_network import *
from .test_game_logic import *
from .test_integration import *
from .test_arcade_api import *
from .test_minimal_multiplayer import *

__all__ = [
    'test_room_discovery',
    'test_host_client_connection',
    'test_message_serialization',
    'run_all_tests',
    'MultiplayerTestSuite',
    'NetworkTestSuite',
    'GameLogicTestSuite',
    'test_imports',
    'test_game_integration',
    'test_network_functionality',
    'test_arcade_api'
]
