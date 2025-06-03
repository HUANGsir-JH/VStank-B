"""
重构后多人联机模块测试

测试新的1对1网络架构
"""

import sys
import os
import time
import threading

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multiplayer.game_host import GameHost
from multiplayer.game_client import GameClient
from multiplayer.room_discovery import RoomDiscovery
from multiplayer.messages import MessageFactory, MessageType


def test_basic_functionality():
    """测试基本功能"""
    print("=" * 60)
    print("重构后多人联机模块基本功能测试")
    print("=" * 60)
    
    # 创建主机和客户端
    host = GameHost(host_port=12350)  # 使用不同端口避免冲突
    client = GameClient()
    
    print(f"✓ 主机创建成功，端口: {host.host_port}")
    print(f"✓ 当前玩家数: {host.get_current_player_count()}")
    print(f"✓ 房间是否已满: {host.is_room_full()}")
    
    # 设置回调函数
    def on_client_join(client_id, player_name):
        print(f"📥 客户端加入: {player_name} (ID: {client_id})")
    
    def on_client_leave(client_id, reason):
        print(f"📤 客户端离开: {client_id} (原因: {reason})")
    
    def on_input_received(client_id, keys_pressed, keys_released):
        print(f"🎮 收到输入: {client_id} - 按下: {keys_pressed}, 释放: {keys_released}")
    
    def on_connection(player_id):
        print(f"🔗 客户端连接成功: {player_id}")
    
    def on_disconnection(reason):
        print(f"❌ 客户端断开连接: {reason}")
    
    def on_game_state(state):
        print(f"🎯 收到游戏状态更新: {len(state.get('tanks', []))} 个坦克")
    
    host.set_callbacks(
        client_join=on_client_join,
        client_leave=on_client_leave,
        input_received=on_input_received
    )
    
    client.set_callbacks(
        connection=on_connection,
        disconnection=on_disconnection,
        game_state=on_game_state
    )
    
    try:
        # 启动主机
        print("\n🚀 启动主机...")
        success = host.start_hosting("测试房间", "测试主机")
        if not success:
            print("❌ 主机启动失败")
            return
        
        time.sleep(0.5)  # 等待主机完全启动
        
        # 客户端连接
        print("🔌 客户端尝试连接...")
        success = client.connect_to_host("127.0.0.1", 12350, "测试玩家")
        if not success:
            print("❌ 客户端连接失败")
            return
        
        time.sleep(0.5)  # 等待连接建立
        
        # 测试输入发送
        print("\n🎮 测试输入发送...")
        client.send_key_press("W")
        client.send_key_press("SPACE")
        time.sleep(0.1)
        client.send_key_release("W")
        
        time.sleep(0.5)  # 等待消息处理
        
        # 测试游戏状态发送
        print("\n📡 测试游戏状态发送...")
        test_game_state = {
            "tanks": [
                {"player_id": "host", "x": 100, "y": 200, "angle": 0, "health": 5},
                {"player_id": client.player_id, "x": 300, "y": 400, "angle": 180, "health": 3}
            ],
            "bullets": [
                {"x": 150, "y": 250, "angle": 45, "owner": "host"}
            ],
            "scores": {"host": 1, client.player_id: 0}
        }
        host.send_game_state(test_game_state)
        
        time.sleep(0.5)  # 等待消息处理
        
        print("\n✅ 基本功能测试完成")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理资源
        print("\n🧹 清理资源...")
        client.disconnect()
        host.stop_hosting()
        time.sleep(0.5)


def test_room_discovery():
    """测试房间发现功能"""
    print("\n" + "=" * 60)
    print("房间发现功能测试")
    print("=" * 60)
    
    # 创建房间发现实例
    discovery = RoomDiscovery(discovery_port=12351)
    
    discovered_rooms = []
    
    def on_rooms_updated(rooms):
        nonlocal discovered_rooms
        discovered_rooms = rooms
        print(f"🔍 发现房间数量: {len(rooms)}")
        for room in rooms:
            print(f"   - {room}")
    
    try:
        # 启动房间发现
        print("🔍 启动房间发现...")
        success = discovery.start_discovery(on_rooms_updated)
        if not success:
            print("❌ 房间发现启动失败")
            return
        
        # 启动房间广播（模拟主机）
        print("📡 启动房间广播...")
        success = discovery.start_advertising("测试房间", "测试主机")
        if not success:
            print("❌ 房间广播启动失败")
            return
        
        # 等待发现
        print("⏳ 等待房间发现...")
        time.sleep(3.0)
        
        # 检查结果
        if discovered_rooms:
            print(f"✅ 成功发现 {len(discovered_rooms)} 个房间")
        else:
            print("⚠️ 未发现任何房间")
        
    except Exception as e:
        print(f"❌ 房间发现测试出现错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理资源
        print("🧹 停止房间发现...")
        discovery.stop_discovery()
        discovery.stop_advertising()


def test_message_protocol():
    """测试消息协议"""
    print("\n" + "=" * 60)
    print("消息协议测试")
    print("=" * 60)
    
    try:
        # 测试各种消息类型
        print("📝 测试消息创建和序列化...")
        
        # 房间广播消息
        room_msg = MessageFactory.create_room_advertise("测试房间", "测试主机")
        room_bytes = room_msg.to_bytes()
        room_restored = room_msg.from_bytes(room_bytes)
        assert room_restored.type == MessageType.ROOM_ADVERTISE
        print("✓ 房间广播消息")
        
        # 加入请求消息
        join_msg = MessageFactory.create_join_request("测试玩家")
        join_bytes = join_msg.to_bytes()
        join_restored = join_msg.from_bytes(join_bytes)
        assert join_restored.type == MessageType.JOIN_REQUEST
        print("✓ 加入请求消息")
        
        # 玩家输入消息
        input_msg = MessageFactory.create_player_input(["W", "SPACE"], ["A"])
        input_bytes = input_msg.to_bytes()
        input_restored = input_msg.from_bytes(input_bytes)
        assert input_restored.type == MessageType.PLAYER_INPUT
        print("✓ 玩家输入消息")
        
        # 游戏状态消息
        tanks = [{"player_id": "host", "x": 100, "y": 200}]
        bullets = [{"x": 150, "y": 250, "owner": "host"}]
        scores = {"host": 1, "client": 0}
        state_msg = MessageFactory.create_game_state(tanks, bullets, scores)
        state_bytes = state_msg.to_bytes()
        state_restored = state_msg.from_bytes(state_bytes)
        assert state_restored.type == MessageType.GAME_STATE
        print("✓ 游戏状态消息")
        
        print("✅ 消息协议测试完成")
        
    except Exception as e:
        print(f"❌ 消息协议测试出现错误: {e}")
        import traceback
        traceback.print_exc()


def test_concurrent_connections():
    """测试并发连接处理"""
    print("\n" + "=" * 60)
    print("并发连接测试")
    print("=" * 60)
    
    host = GameHost(host_port=12352)
    
    connection_results = []
    
    def try_connect(client_id):
        """尝试连接的线程函数"""
        client = GameClient()
        
        def on_connection(player_id):
            connection_results.append(f"客户端{client_id}连接成功: {player_id}")
        
        def on_disconnection(reason):
            connection_results.append(f"客户端{client_id}断开: {reason}")
        
        client.set_callbacks(connection=on_connection, disconnection=on_disconnection)
        
        success = client.connect_to_host("127.0.0.1", 12352, f"玩家{client_id}")
        if success:
            time.sleep(1.0)  # 保持连接一段时间
        client.disconnect()
    
    try:
        # 启动主机
        print("🚀 启动主机...")
        success = host.start_hosting("并发测试房间", "测试主机")
        if not success:
            print("❌ 主机启动失败")
            return
        
        time.sleep(0.5)
        
        # 启动多个客户端尝试连接
        print("🔌 启动多个客户端连接...")
        threads = []
        for i in range(3):  # 尝试3个客户端连接
            thread = threading.Thread(target=try_connect, args=(i+1,))
            threads.append(thread)
            thread.start()
            time.sleep(0.1)  # 稍微错开连接时间
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        time.sleep(0.5)
        
        # 检查结果
        print("\n📊 连接结果:")
        for result in connection_results:
            print(f"   {result}")
        
        # 验证只有一个客户端成功连接（1对1模式）
        success_count = sum(1 for r in connection_results if "连接成功" in r)
        if success_count == 1:
            print("✅ 1对1连接限制正常工作")
        else:
            print(f"⚠️ 预期1个成功连接，实际{success_count}个")
        
    except Exception as e:
        print(f"❌ 并发连接测试出现错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理资源
        print("🧹 清理资源...")
        host.stop_hosting()


def main():
    """主测试函数"""
    print("🧪 开始重构后多人联机模块测试")
    print("=" * 80)
    
    # 运行各项测试
    test_basic_functionality()
    test_room_discovery()
    test_message_protocol()
    test_concurrent_connections()
    
    print("\n" + "=" * 80)
    print("🎉 所有测试完成！")


if __name__ == "__main__":
    main()
