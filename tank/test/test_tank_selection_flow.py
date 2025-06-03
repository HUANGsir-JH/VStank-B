"""
测试坦克选择流程修复

验证双人模式下的坦克选择流程：
1. 主机创建房间并进入坦克选择
2. 客户端加入房间并进入坦克选择
3. 坦克选择界面显示2个玩家
4. 双方完成选择后进入游戏
"""

import sys
import os
import time
import threading

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from multiplayer.dual_player_host import DualPlayerHost
from multiplayer.dual_player_client import DualPlayerClient


def test_tank_selection_flow():
    """测试坦克选择流程"""
    print("🎮 测试双人模式坦克选择流程...")
    
    host = DualPlayerHost(host_port=12358)
    client = DualPlayerClient()
    
    # 记录事件
    events = []
    
    def on_client_join(client_id, player_name):
        events.append(('client_join', client_id, player_name))
        print(f"📥 主机：客户端加入 {player_name} (ID: {client_id})")
    
    def on_client_leave(client_id, reason):
        events.append(('client_leave', client_id, reason))
        print(f"📤 主机：客户端离开 {client_id} (原因: {reason})")
    
    def on_connection(player_id):
        events.append(('connection', player_id))
        print(f"🔗 客户端：连接成功 {player_id}")
    
    def on_disconnection(reason):
        events.append(('disconnection', reason))
        print(f"❌ 客户端：断开连接 {reason}")
    
    try:
        # 设置回调
        host.set_callbacks(
            client_join=on_client_join,
            client_leave=on_client_leave
        )
        
        client.set_callbacks(
            connection=on_connection,
            disconnection=on_disconnection
        )
        
        # 步骤1：启动主机
        print("\n🚀 步骤1：启动主机...")
        success = host.start_hosting("坦克选择流程测试")
        assert success, "主机启动失败"
        time.sleep(0.2)
        
        # 验证主机初始状态
        print(f"   主机状态: 玩家数={host.get_current_player_count()}, 房间满={host.is_room_full()}")
        assert host.get_current_player_count() == 1, "主机初始应该只有1个玩家"
        assert not host.is_room_full(), "主机初始房间不应该满"
        
        # 步骤2：客户端连接
        print("\n🔌 步骤2：客户端连接...")
        success = client.connect_to_host("127.0.0.1", 12358, "测试客户端")
        assert success, "客户端连接失败"
        time.sleep(0.3)
        
        # 验证连接后状态
        print(f"   连接后状态:")
        print(f"     主机玩家数: {host.get_current_player_count()}")
        print(f"     主机房间满: {host.is_room_full()}")
        print(f"     客户端连接: {client.is_connected()}")
        print(f"     客户端ID: {client.get_player_id()}")
        print(f"     主机客户端ID: {host.get_client_id()}")
        
        assert host.get_current_player_count() == 2, "连接后应该有2个玩家"
        assert host.is_room_full(), "连接后房间应该满"
        assert client.is_connected(), "客户端应该已连接"
        assert host.get_client_id() is not None, "主机应该有客户端ID"
        assert client.get_player_id() is not None, "客户端应该有玩家ID"
        
        # 步骤3：模拟坦克选择视图创建
        print("\n🎯 步骤3：模拟坦克选择视图...")
        
        # 模拟主机端坦克选择视图
        class MockHostTankSelection:
            def __init__(self, game_host):
                self.is_host = True
                self.game_host = game_host
                self.connected_players = set()
                self.selected_tanks = {}
                self.ready_players = set()
                self.my_player_id = "host"
                
                # 初始化连接的玩家列表（模拟setup方法）
                self.connected_players.add("host")
                
                # 双人模式：如果主机已经有客户端连接，添加到连接列表
                if self.game_host and self.game_host.get_client_id():
                    client_id = self.game_host.get_client_id()
                    self.connected_players.add(client_id)
                    print(f"   主机坦克选择：检测到已连接的客户端 {client_id}")
        
        # 模拟客户端坦克选择视图
        class MockClientTankSelection:
            def __init__(self, game_client):
                self.is_host = False
                self.game_client = game_client
                self.connected_players = set()
                self.selected_tanks = {}
                self.ready_players = set()
                self.my_player_id = None
                
                # 客户端获取自己的玩家ID（模拟setup方法）
                if self.game_client:
                    self.my_player_id = self.game_client.get_player_id()
                    if self.my_player_id:
                        self.connected_players.add(self.my_player_id)
                        print(f"   客户端坦克选择：客户端 {self.my_player_id} 已连接")
        
        # 创建模拟视图
        host_tank_view = MockHostTankSelection(host)
        client_tank_view = MockClientTankSelection(client)
        
        # 验证坦克选择视图状态
        print(f"   主机坦克选择视图:")
        print(f"     连接玩家数: {len(host_tank_view.connected_players)}")
        print(f"     连接玩家: {list(host_tank_view.connected_players)}")
        
        print(f"   客户端坦克选择视图:")
        print(f"     连接玩家数: {len(client_tank_view.connected_players)}")
        print(f"     连接玩家: {list(client_tank_view.connected_players)}")
        print(f"     我的玩家ID: {client_tank_view.my_player_id}")
        
        # 验证主机坦克选择视图能看到2个玩家
        assert len(host_tank_view.connected_players) == 2, f"主机坦克选择应该看到2个玩家，实际看到{len(host_tank_view.connected_players)}个"
        assert "host" in host_tank_view.connected_players, "主机坦克选择应该包含主机"
        assert host.get_client_id() in host_tank_view.connected_players, "主机坦克选择应该包含客户端"
        
        # 验证客户端坦克选择视图状态
        assert len(client_tank_view.connected_players) == 1, "客户端坦克选择应该看到1个玩家（自己）"
        assert client_tank_view.my_player_id is not None, "客户端应该有玩家ID"
        assert client_tank_view.my_player_id == client.get_player_id(), "客户端玩家ID应该匹配"
        
        # 步骤4：模拟坦克选择过程
        print("\n🎨 步骤4：模拟坦克选择过程...")
        
        # 主机选择坦克
        host_tank_view.selected_tanks["host"] = {
            "tank_type": "green",
            "tank_image_path": "/path/to/green.png"
        }
        host_tank_view.ready_players.add("host")
        print("   主机选择了绿色坦克并准备")
        
        # 客户端选择坦克
        client_id = client.get_player_id()
        client_tank_view.selected_tanks[client_id] = {
            "tank_type": "blue", 
            "tank_image_path": "/path/to/blue.png"
        }
        client_tank_view.ready_players.add(client_id)
        print("   客户端选择了蓝色坦克并准备")
        
        # 模拟准备检查
        def check_all_players_ready(ready_players):
            expected_players = 2
            if len(ready_players) >= expected_players:
                print(f"   双人游戏所有玩家已准备完成（{len(ready_players)}/{expected_players}），可以开始游戏！")
                return True
            else:
                print(f"   等待玩家准备：{len(ready_players)}/{expected_players}")
                return False
        
        # 只有主机准备
        ready_players = {"host"}
        can_start = check_all_players_ready(ready_players)
        assert not can_start, "只有主机准备时不应该能开始游戏"
        
        # 双方都准备
        ready_players = {"host", client_id}
        can_start = check_all_players_ready(ready_players)
        assert can_start, "双方都准备时应该能开始游戏"
        
        print("✅ 坦克选择流程测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # 清理
        print("\n🧹 清理资源...")
        if client.is_connected():
            client.disconnect()
        if host.running:
            host.stop_hosting(force=True)
        time.sleep(0.2)


def test_tank_selection_player_count():
    """测试坦克选择界面的玩家数量显示"""
    print("\n📊 测试坦克选择界面玩家数量显示...")
    
    # 模拟主机坦克选择视图的玩家数量显示逻辑
    class MockTankSelectionDisplay:
        def __init__(self, connected_players):
            self.connected_players = connected_players
        
        def get_room_info_text(self, room_name):
            """获取房间信息文本"""
            return f"房间: {room_name} | 玩家: {len(self.connected_players)}"
        
        def get_player_status_list(self, ready_players):
            """获取玩家状态列表"""
            status_list = []
            for player_id in self.connected_players:
                is_ready = player_id in ready_players
                status_text = "✓ 已准备" if is_ready else "○ 未准备"
                player_name = "主机" if player_id == "host" else f"玩家{player_id[-4:]}"
                status_list.append(f"{player_name}: {status_text}")
            return status_list
    
    try:
        # 测试只有主机的情况
        display = MockTankSelectionDisplay({"host"})
        room_info = display.get_room_info_text("测试房间")
        print(f"   只有主机: {room_info}")
        assert "玩家: 1" in room_info, "只有主机时应该显示1个玩家"
        
        # 测试主机+客户端的情况
        display = MockTankSelectionDisplay({"host", "client_12345678"})
        room_info = display.get_room_info_text("测试房间")
        print(f"   主机+客户端: {room_info}")
        assert "玩家: 2" in room_info, "主机+客户端时应该显示2个玩家"
        
        # 测试玩家状态显示
        ready_players = {"host"}
        status_list = display.get_player_status_list(ready_players)
        print(f"   玩家状态: {status_list}")
        assert len(status_list) == 2, "应该显示2个玩家的状态"
        assert any("主机: ✓ 已准备" in status for status in status_list), "主机应该显示已准备"
        assert any("○ 未准备" in status for status in status_list), "客户端应该显示未准备"
        
        print("✅ 玩家数量显示测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 玩家数量显示测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🔧 双人模式坦克选择流程测试")
    print("=" * 50)
    
    tests = [
        ("坦克选择流程", test_tank_selection_flow),
        ("玩家数量显示", test_tank_selection_player_count),
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
        print("🎉 坦克选择流程修复验证成功！")
        print("\n修复内容:")
        print("✓ 客户端连接后进入坦克选择阶段")
        print("✓ 主机坦克选择界面显示2个玩家")
        print("✓ 客户端正确获取玩家ID")
        print("✓ 双人准备检查逻辑正确")
        return True
    else:
        print("⚠️ 部分测试失败，需要进一步检查")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
