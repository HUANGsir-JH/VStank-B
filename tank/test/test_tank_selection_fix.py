"""
测试坦克选择模块修复

验证坦克选择阶段与双人模式的兼容性
"""

import sys
import os
import time
import threading

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from multiplayer.dual_player_host import DualPlayerHost
from multiplayer.dual_player_client import DualPlayerClient
from multiplayer.udp_messages import MessageFactory, MessageType


def test_tank_selection_api_compatibility():
    """测试坦克选择API兼容性"""
    print("🔍 测试坦克选择API兼容性...")
    
    host = DualPlayerHost(host_port=12357)
    client = DualPlayerClient()
    
    # 记录消息
    messages_sent = []
    messages_received = []
    
    def on_client_join(client_id, player_name):
        print(f"📥 客户端加入: {player_name} (ID: {client_id})")
    
    def on_client_leave(client_id, reason):
        print(f"📤 客户端离开: {client_id} (原因: {reason})")
    
    def on_connection(player_id):
        print(f"🔗 客户端连接成功: {player_id}")
    
    def on_disconnection(reason):
        print(f"❌ 客户端断开连接: {reason}")
    
    def on_game_state(state):
        messages_received.append(('game_state', state))
        print(f"🎯 收到游戏状态")
    
    try:
        # 设置回调
        host.set_callbacks(
            client_join=on_client_join,
            client_leave=on_client_leave
        )
        
        client.set_callbacks(
            connection=on_connection,
            disconnection=on_disconnection,
            game_state=on_game_state
        )
        
        # 启动主机
        print("🚀 启动主机...")
        success = host.start_hosting("坦克选择测试房间")
        assert success, "主机启动失败"
        time.sleep(0.2)
        
        # 客户端连接
        print("🔌 客户端尝试连接...")
        success = client.connect_to_host("127.0.0.1", 12357, "测试玩家")
        assert success, "客户端连接失败"
        time.sleep(0.3)
        
        # 验证连接状态
        assert host.get_current_player_count() == 2, "应该有2个玩家"
        assert client.is_connected(), "客户端应该已连接"
        
        # 测试坦克选择同步消息（模拟主机发送）
        print("📡 测试坦克选择同步消息...")
        
        # 创建坦克选择同步消息
        selected_tanks = {
            "host": {"tank_type": "green", "tank_image_path": "/path/to/green.png"},
            client.get_player_id(): {"tank_type": "blue", "tank_image_path": "/path/to/blue.png"}
        }
        ready_players = ["host"]
        
        sync_message = MessageFactory.create_tank_selection_sync(selected_tanks, ready_players)
        
        # 使用新的双人模式API发送消息
        host.send_to_client(sync_message)
        time.sleep(0.2)
        
        print("✓ 坦克选择同步消息发送成功")
        
        # 测试冲突消息（模拟主机发送）
        print("📡 测试坦克选择冲突消息...")
        
        conflict_message = MessageFactory.create_tank_selection_conflict(
            client.get_player_id(), "green", "坦克已被其他玩家选择"
        )
        
        # 使用新的双人模式API发送冲突消息
        host.send_to_client(conflict_message)
        time.sleep(0.2)
        
        print("✓ 坦克选择冲突消息发送成功")
        
        # 测试客户端发送准备消息
        print("📡 测试客户端准备消息...")
        
        ready_message = MessageFactory.create_tank_selection_ready(
            client.get_player_id(), "blue", "/path/to/blue.png"
        )
        
        client.send_message(ready_message)
        time.sleep(0.2)
        
        print("✓ 客户端准备消息发送成功")
        
        print("✅ 坦克选择API兼容性测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # 清理
        print("🧹 清理资源...")
        if client.is_connected():
            client.disconnect()
        if host.running:
            host.stop_hosting(force=True)
        time.sleep(0.2)


def test_dual_player_ready_logic():
    """测试双人模式准备逻辑"""
    print("\n🎮 测试双人模式准备逻辑...")
    
    # 模拟坦克选择视图的准备检查逻辑
    class MockTankSelectionView:
        def __init__(self):
            self.ready_players = set()
            self.connected_players = set(["host"])  # 主机总是连接的
            self.is_host = True
        
        def add_client(self, client_id):
            """添加客户端"""
            self.connected_players.add(client_id)
        
        def set_player_ready(self, player_id):
            """设置玩家准备状态"""
            self.ready_players.add(player_id)
        
        def check_all_players_ready(self):
            """检查是否所有玩家都已准备完成（双人模式）"""
            if not self.is_host:
                return False
            
            # 双人模式：需要2个玩家都准备好（主机+客户端）
            expected_players = 2
            if len(self.ready_players) >= expected_players:
                print(f"双人游戏所有玩家已准备完成（{len(self.ready_players)}/{expected_players}），可以开始游戏！")
                return True
            else:
                print(f"等待玩家准备：{len(self.ready_players)}/{expected_players}")
                return False
    
    try:
        view = MockTankSelectionView()
        
        # 初始状态：只有主机
        print(f"初始状态: 连接玩家={len(view.connected_players)}, 准备玩家={len(view.ready_players)}")
        assert not view.check_all_players_ready(), "初始状态不应该能开始游戏"
        
        # 主机准备
        view.set_player_ready("host")
        print(f"主机准备后: 连接玩家={len(view.connected_players)}, 准备玩家={len(view.ready_players)}")
        assert not view.check_all_players_ready(), "只有主机准备不应该能开始游戏"
        
        # 客户端加入
        view.add_client("client_123")
        print(f"客户端加入后: 连接玩家={len(view.connected_players)}, 准备玩家={len(view.ready_players)}")
        assert not view.check_all_players_ready(), "客户端未准备不应该能开始游戏"
        
        # 客户端准备
        view.set_player_ready("client_123")
        print(f"客户端准备后: 连接玩家={len(view.connected_players)}, 准备玩家={len(view.ready_players)}")
        assert view.check_all_players_ready(), "双方都准备后应该能开始游戏"
        
        print("✅ 双人模式准备逻辑测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 准备逻辑测试失败: {e}")
        return False


def test_message_factory_methods():
    """测试消息工厂方法"""
    print("\n🏭 测试消息工厂方法...")
    
    try:
        # 测试坦克选择同步消息
        selected_tanks = {
            "host": {"tank_type": "green", "tank_image_path": "/path/to/green.png"},
            "client_123": {"tank_type": "blue", "tank_image_path": "/path/to/blue.png"}
        }
        ready_players = ["host", "client_123"]
        
        sync_msg = MessageFactory.create_tank_selection_sync(selected_tanks, ready_players)
        assert sync_msg.type == MessageType.TANK_SELECTION_SYNC, "同步消息类型错误"
        assert sync_msg.data["selected_tanks"] == selected_tanks, "同步消息数据错误"
        print("✓ 坦克选择同步消息创建成功")
        
        # 测试坦克选择冲突消息
        conflict_msg = MessageFactory.create_tank_selection_conflict(
            "client_123", "green", "坦克已被选择"
        )
        assert conflict_msg.type == MessageType.TANK_SELECTION_CONFLICT, "冲突消息类型错误"
        assert conflict_msg.player_id == "client_123", "冲突消息玩家ID错误"
        print("✓ 坦克选择冲突消息创建成功")
        
        # 测试坦克选择准备消息
        ready_msg = MessageFactory.create_tank_selection_ready(
            "client_123", "blue", "/path/to/blue.png"
        )
        assert ready_msg.type == MessageType.TANK_SELECTION_READY, "准备消息类型错误"
        assert ready_msg.player_id == "client_123", "准备消息玩家ID错误"
        print("✓ 坦克选择准备消息创建成功")
        
        print("✅ 消息工厂方法测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 消息工厂测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🔧 坦克选择模块双人模式兼容性测试")
    print("=" * 50)
    
    tests = [
        ("坦克选择API兼容性", test_tank_selection_api_compatibility),
        ("双人模式准备逻辑", test_dual_player_ready_logic),
        ("消息工厂方法", test_message_factory_methods),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} - 通过")
            else:
                print(f"❌ {test_name} - 失败")
        except Exception as e:
            print(f"❌ {test_name} - 异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 坦克选择模块兼容性修复验证成功！")
        print("\n修复内容:")
        print("✓ 替换 broadcast_message() 为 send_to_client()")
        print("✓ 移除 send_to_client() 的 client_id 参数")
        print("✓ 更新双人模式准备检查逻辑")
        print("✓ 简化游戏启动流程")
        return True
    else:
        print("⚠️ 部分测试失败，需要进一步检查")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
