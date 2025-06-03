"""
单台电脑双人联机测试方案

这个脚本提供了在单台电脑上测试双人联机功能的完整解决方案，
包括端口管理、进程隔离和自动化测试。
"""

import sys
import os
import time
import threading
import subprocess
import socket
from typing import List, Tuple

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multiplayer.game_host import GameHost
from multiplayer.game_client import GameClient
from multiplayer.room_discovery import RoomDiscovery


class LocalMultiplayerTester:
    """单台电脑双人联机测试器"""
    
    def __init__(self):
        self.base_port = 13000  # 使用不同的端口避免冲突
        self.host_process = None
        self.client_process = None
        self.test_results = []
    
    def find_available_ports(self, count: int = 2) -> List[int]:
        """查找可用端口"""
        available_ports = []
        port = self.base_port
        
        while len(available_ports) < count:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                    sock.bind(('127.0.0.1', port))
                    available_ports.append(port)
            except OSError:
                pass
            port += 1
        
        return available_ports
    
    def test_port_availability(self):
        """测试端口可用性"""
        print("🔍 检查端口可用性...")
        
        ports = self.find_available_ports(5)
        print(f"✅ 找到可用端口: {ports}")
        
        # 测试端口占用和释放
        test_port = ports[0]
        
        # 占用端口
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('127.0.0.1', test_port))
        print(f"✅ 端口 {test_port} 成功占用")
        
        # 释放端口
        sock.close()
        print(f"✅ 端口 {test_port} 成功释放")
        
        return True
    
    def test_simultaneous_connections(self):
        """测试同时连接"""
        print("\n🔗 测试同时连接...")
        
        ports = self.find_available_ports(2)
        host_port = ports[0]
        discovery_port = ports[1]
        
        # 创建主机和客户端
        host = GameHost(host_port)
        client = GameClient()
        
        # 设置事件记录
        events = []
        
        def on_client_join(client_id, player_name):
            events.append(('join', client_id, player_name))
            print(f"📥 主机：客户端加入 {player_name} ({client_id})")
        
        def on_client_leave(client_id, reason):
            events.append(('leave', client_id, reason))
            print(f"📤 主机：客户端离开 {client_id} ({reason})")
        
        def on_connection(player_id):
            events.append(('connected', player_id))
            print(f"🔗 客户端：连接成功 {player_id}")
        
        def on_disconnection(reason):
            events.append(('disconnected', reason))
            print(f"❌ 客户端：断开连接 {reason}")
        
        host.set_callbacks(client_join=on_client_join, client_leave=on_client_leave)
        client.set_callbacks(connection=on_connection, disconnection=on_disconnection)
        
        try:
            # 启动主机
            print(f"🚀 启动主机 (端口 {host_port})...")
            success = host.start_hosting("测试房间", "测试主机")
            if not success:
                print("❌ 主机启动失败")
                return False
            
            time.sleep(0.5)  # 等待主机完全启动
            
            # 客户端连接
            print("🔌 客户端连接...")
            success = client.connect_to_host("127.0.0.1", host_port, "测试客户端")
            if not success:
                print("❌ 客户端连接失败")
                return False
            
            time.sleep(1.0)  # 等待连接稳定
            
            # 验证连接状态
            if host.get_current_player_count() == 2 and client.is_connected():
                print("✅ 同时连接测试成功")
                return True
            else:
                print("❌ 连接状态验证失败")
                return False
        
        finally:
            # 清理资源
            client.disconnect()
            host.stop_hosting()
            time.sleep(0.5)
    
    def test_message_exchange(self):
        """测试消息交换"""
        print("\n💬 测试消息交换...")
        
        ports = self.find_available_ports(2)
        host_port = ports[0]
        
        host = GameHost(host_port)
        client = GameClient()
        
        # 消息记录
        received_messages = []
        
        def on_input_received(client_id, keys_pressed, keys_released):
            received_messages.append(('input', client_id, keys_pressed, keys_released))
            print(f"🎮 主机收到输入: {client_id} - 按下:{keys_pressed}, 释放:{keys_released}")
        
        def on_game_state(state):
            received_messages.append(('state', state))
            print(f"🎯 客户端收到状态: {len(state.get('tanks', []))} 个坦克")
        
        host.set_callbacks(input_received=on_input_received)
        client.set_callbacks(game_state=on_game_state)
        
        try:
            # 建立连接
            host.start_hosting("消息测试房间", "测试主机")
            time.sleep(0.5)
            
            client.connect_to_host("127.0.0.1", host_port, "测试客户端")
            time.sleep(1.0)
            
            # 测试客户端发送输入
            print("📤 客户端发送输入...")
            client.send_key_press("W")
            client.send_key_press("SPACE")
            time.sleep(0.1)
            client.send_key_release("W")
            time.sleep(0.5)
            
            # 测试主机发送游戏状态
            print("📤 主机发送游戏状态...")
            test_state = {
                "tanks": [
                    {"player_id": "host", "x": 100, "y": 200},
                    {"player_id": client.get_player_id(), "x": 300, "y": 400}
                ],
                "bullets": [],
                "scores": {"host": 0, client.get_player_id(): 0}
            }
            host.send_game_state(test_state)
            time.sleep(0.5)
            
            # 验证消息接收
            input_received = any(msg[0] == 'input' for msg in received_messages)
            state_received = any(msg[0] == 'state' for msg in received_messages)
            
            if input_received and state_received:
                print("✅ 消息交换测试成功")
                return True
            else:
                print(f"❌ 消息交换测试失败 - 输入:{input_received}, 状态:{state_received}")
                return False
        
        finally:
            client.disconnect()
            host.stop_hosting()
            time.sleep(0.5)
    
    def test_room_discovery(self):
        """测试房间发现"""
        print("\n🔍 测试房间发现...")
        
        ports = self.find_available_ports(3)
        discovery_port = ports[0]
        host_port = ports[1]
        
        # 创建房间发现实例
        advertiser = RoomDiscovery(discovery_port)
        discoverer = RoomDiscovery(discovery_port)
        
        discovered_rooms = []
        
        def on_rooms_updated(rooms):
            nonlocal discovered_rooms
            discovered_rooms = rooms
            print(f"🔍 发现房间: {len(rooms)} 个")
            for room in rooms:
                print(f"   - {room.room_name} ({room.host_name})")
        
        try:
            # 启动房间发现
            print("🔍 启动房间搜索...")
            discoverer.start_discovery(on_rooms_updated)
            time.sleep(0.5)
            
            # 启动房间广播
            print("📡 启动房间广播...")
            advertiser.start_advertising("测试发现房间", "测试主机")
            time.sleep(3.0)  # 等待发现
            
            # 验证发现结果
            if discovered_rooms:
                print("✅ 房间发现测试成功")
                return True
            else:
                print("❌ 房间发现测试失败 - 未发现房间")
                return False
        
        finally:
            discoverer.stop_discovery()
            advertiser.stop_advertising()
            time.sleep(0.5)
    
    def test_connection_limits(self):
        """测试连接限制"""
        print("\n🚫 测试连接限制...")
        
        ports = self.find_available_ports(2)
        host_port = ports[0]
        
        host = GameHost(host_port)
        client1 = GameClient()
        client2 = GameClient()
        
        connection_results = []
        
        def on_connection1(player_id):
            connection_results.append(('client1', 'connected', player_id))
        
        def on_connection2(player_id):
            connection_results.append(('client2', 'connected', player_id))
        
        def on_disconnection1(reason):
            connection_results.append(('client1', 'disconnected', reason))
        
        def on_disconnection2(reason):
            connection_results.append(('client2', 'disconnected', reason))
        
        client1.set_callbacks(connection=on_connection1, disconnection=on_disconnection1)
        client2.set_callbacks(connection=on_connection2, disconnection=on_disconnection2)
        
        try:
            # 启动主机
            host.start_hosting("限制测试房间", "测试主机")
            time.sleep(0.5)
            
            # 第一个客户端连接
            print("🔌 第一个客户端连接...")
            success1 = client1.connect_to_host("127.0.0.1", host_port, "客户端1")
            time.sleep(0.5)
            
            # 第二个客户端连接（应该被拒绝）
            print("🔌 第二个客户端连接...")
            success2 = client2.connect_to_host("127.0.0.1", host_port, "客户端2")
            time.sleep(0.5)
            
            # 验证结果
            client1_connected = any(r[0] == 'client1' and r[1] == 'connected' for r in connection_results)
            client2_connected = any(r[0] == 'client2' and r[1] == 'connected' for r in connection_results)
            
            if client1_connected and not client2_connected:
                print("✅ 连接限制测试成功 - 1对1限制正常工作")
                return True
            else:
                print(f"❌ 连接限制测试失败 - 客户端1:{client1_connected}, 客户端2:{client2_connected}")
                return False
        
        finally:
            client1.disconnect()
            client2.disconnect()
            host.stop_hosting()
            time.sleep(0.5)
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🧪 开始单台电脑双人联机测试")
        print("=" * 60)
        
        tests = [
            ("端口可用性", self.test_port_availability),
            ("同时连接", self.test_simultaneous_connections),
            ("消息交换", self.test_message_exchange),
            ("房间发现", self.test_room_discovery),
            ("连接限制", self.test_connection_limits)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🔧 测试: {test_name}")
            print("-" * 40)
            
            try:
                result = test_func()
                if result:
                    print(f"✅ {test_name} - 通过")
                    passed += 1
                else:
                    print(f"❌ {test_name} - 失败")
            except Exception as e:
                print(f"❌ {test_name} - 异常: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n" + "=" * 60)
        print(f"📊 测试结果: {passed}/{total} 测试通过")
        
        if passed == total:
            print("🎉 所有测试通过！单台电脑双人联机功能正常")
        else:
            print("⚠️ 部分测试失败，请检查网络配置")
        
        return passed == total


def main():
    """主函数"""
    print("🎮 单台电脑双人联机测试工具")
    print("=" * 80)
    
    tester = LocalMultiplayerTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n📋 单台电脑测试指南:")
        print("1. 启动游戏: python tank/main.py")
        print("2. 选择多人联机 (按键2)")
        print("3. 创建房间 (按键H)")
        print("4. 在另一个终端启动第二个游戏实例")
        print("5. 第二个实例选择多人联机，加入房间")
        print("6. 开始双人对战！")
        
        print("\n💡 提示:")
        print("- 使用不同的端口避免冲突")
        print("- 确保防火墙允许本地连接")
        print("- 可以使用虚拟机测试真实网络环境")
    
    return success


if __name__ == "__main__":
    main()
