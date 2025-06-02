"""
多人游戏模块测试

用于测试UDP网络功能的基本运行
"""

import time
import threading
import sys
import os
import unittest

# 添加父目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multiplayer.udp_discovery import RoomDiscovery, RoomAdvertiser
from multiplayer.udp_host import GameHost
from multiplayer.udp_client import GameClient
from multiplayer.udp_messages import MessageFactory, UDPMessage


class MultiplayerTestSuite:
    """多人游戏测试套件"""
    
    def __init__(self):
        self.test_results = []
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=== 多人游戏模块测试套件 ===\n")
        
        tests = [
            ("消息序列化测试", self.test_message_serialization),
            ("房间发现测试", self.test_room_discovery),
            ("主机-客户端连接测试", self.test_host_client_connection)
        ]
        
        for test_name, test_func in tests:
            print(f"运行 {test_name}...")
            try:
                result = test_func()
                self.test_results.append((test_name, "PASS", result))
                print(f"✅ {test_name} 通过\n")
            except Exception as e:
                self.test_results.append((test_name, "FAIL", str(e)))
                print(f"❌ {test_name} 失败: {e}\n")
        
        self.print_summary()
    
    def print_summary(self):
        """打印测试摘要"""
        print("=== 测试摘要 ===")
        passed = sum(1 for _, status, _ in self.test_results if status == "PASS")
        total = len(self.test_results)
        
        for test_name, status, result in self.test_results:
            status_icon = "✅" if status == "PASS" else "❌"
            print(f"{status_icon} {test_name}: {status}")
        
        print(f"\n总计: {passed}/{total} 测试通过")
        
        if passed == total:
            print("🎉 所有测试都通过了！")
        else:
            print("⚠️  有测试失败，请检查上述错误信息")
    
    def test_message_serialization(self):
        """测试消息序列化"""
        print("  测试各种消息类型的序列化和反序列化...")
        
        # 测试各种消息类型
        messages = [
            MessageFactory.create_room_advertise("测试房间", 2, 4, "pvp"),
            MessageFactory.create_join_request("测试玩家"),
            MessageFactory.create_join_response(True, "player_123"),
            MessageFactory.create_player_input("player_123", ["W", "SPACE"], ["A"]),
            MessageFactory.create_heartbeat("player_123"),
            MessageFactory.create_disconnect("player_123", "user_quit")
        ]
        
        for i, msg in enumerate(messages):
            # 序列化
            data = msg.to_bytes()
            assert len(data) > 0, f"消息 {i+1} 序列化失败"
            
            # 反序列化
            restored_msg = UDPMessage.from_bytes(data)
            assert restored_msg.type == msg.type, f"消息 {i+1} 类型不匹配"
            assert restored_msg.data == msg.data, f"消息 {i+1} 数据不匹配"
            assert restored_msg.player_id == msg.player_id, f"消息 {i+1} 玩家ID不匹配"
            
            print(f"    消息 {i+1} ({msg.type}): {len(data)} 字节 ✓")
        
        return f"成功测试 {len(messages)} 种消息类型"
    
    def test_room_discovery(self):
        """测试房间发现功能"""
        print("  启动房间广播和发现...")
        
        # 创建房间广播器
        advertiser = RoomAdvertiser()
        advertiser.start_advertising("测试房间", 1, 4, "pvp")
        
        # 创建房间发现器
        discovery = RoomDiscovery()
        discovered_rooms = {}
        
        def on_rooms_updated(rooms):
            discovered_rooms.update(rooms)
            print(f"    发现房间: {len(rooms)} 个")
        
        discovery.set_room_update_callback(on_rooms_updated)
        discovery.start_discovery()
        
        # 等待发现
        print("    等待房间发现...")
        time.sleep(3)
        
        # 验证结果
        assert len(discovered_rooms) > 0, "未发现任何房间"
        
        # 验证房间信息
        for ip, room in discovered_rooms.items():
            assert room.room_name == "测试房间", "房间名称不匹配"
            assert room.current_players == 1, "玩家数量不匹配"
            assert room.max_players == 4, "最大玩家数不匹配"
            print(f"    验证房间 {room.room_name} @ {ip} ✓")
        
        # 清理
        advertiser.stop_advertising()
        discovery.stop_discovery()
        
        return f"成功发现并验证 {len(discovered_rooms)} 个房间"
    
    def test_host_client_connection(self):
        """测试主机-客户端连接"""
        print("  测试主机-客户端连接和通信...")
        
        # 连接状态跟踪
        connection_events = {
            'client_joined': False,
            'client_connected': False,
            'input_received': False,
            'client_left': False
        }
        
        # 创建主机
        host = GameHost()
        
        def on_client_join(client_id, player_name):
            print(f"    客户端加入: {player_name} ({client_id})")
            connection_events['client_joined'] = True
        
        def on_client_leave(client_id, reason):
            print(f"    客户端离开: {client_id} ({reason})")
            connection_events['client_left'] = True
        
        def on_input_received(client_id, keys_pressed, keys_released):
            print(f"    收到输入 {client_id}: 按下={keys_pressed}")
            connection_events['input_received'] = True
        
        host.set_callbacks(
            client_join=on_client_join,
            client_leave=on_client_leave,
            input_received=on_input_received
        )
        
        # 启动主机
        assert host.start_hosting("测试主机房间"), "主机启动失败"
        print("    主机启动成功")
        
        # 等待主机完全启动
        time.sleep(0.5)
        
        # 创建客户端
        client = GameClient()
        
        def on_connected(player_id):
            print(f"    客户端连接成功: {player_id}")
            connection_events['client_connected'] = True
        
        def on_disconnected(reason):
            print(f"    客户端断开连接: {reason}")
        
        client.set_callbacks(
            connection=on_connected,
            disconnection=on_disconnected
        )
        
        # 连接到主机
        assert client.connect_to_host("127.0.0.1", 12346, "测试玩家"), "客户端连接失败"
        print("    客户端连接成功")
        
        # 等待连接建立
        time.sleep(0.5)
        
        # 发送测试输入
        print("    发送测试输入...")
        client.send_key_press("W")
        client.send_key_press("SPACE")
        time.sleep(0.2)
        client.send_key_release("W")
        
        # 等待输入处理
        time.sleep(0.5)
        
        # 断开客户端
        client.disconnect()
        time.sleep(0.5)
        
        # 停止主机
        host.stop_hosting()
        
        # 验证连接事件
        assert connection_events['client_joined'], "客户端加入事件未触发"
        assert connection_events['client_connected'], "客户端连接事件未触发"
        assert connection_events['input_received'], "输入接收事件未触发"
        
        print("    所有连接事件验证通过 ✓")
        
        return "主机-客户端连接和通信测试成功"


def test_room_discovery():
    """独立的房间发现测试函数"""
    suite = MultiplayerTestSuite()
    return suite.test_room_discovery()


def test_host_client_connection():
    """独立的主机-客户端连接测试函数"""
    suite = MultiplayerTestSuite()
    return suite.test_host_client_connection()


def test_message_serialization():
    """独立的消息序列化测试函数"""
    suite = MultiplayerTestSuite()
    return suite.test_message_serialization()


def run_all_tests():
    """运行所有多人游戏测试"""
    suite = MultiplayerTestSuite()
    suite.run_all_tests()


def main():
    """主函数"""
    print("多人游戏模块测试")
    print("=" * 50)
    
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
