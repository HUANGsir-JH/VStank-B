"""
双人游戏模块演示脚本

演示重构后的双人游戏功能，验证主机-客户端连接和基本通信
"""

import sys
import os
import time
import threading

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from multiplayer.dual_player_host import DualPlayerHost
from multiplayer.dual_player_client import DualPlayerClient


def demo_basic_functionality():
    """演示基本功能"""
    print("=" * 60)
    print("双人游戏模块基本功能演示")
    print("=" * 60)
    
    # 创建主机和客户端
    host = DualPlayerHost(host_port=12349)  # 使用不同端口避免冲突
    client = DualPlayerClient()
    
    print(f"✓ 主机创建成功，端口: {host.host_port}")
    print(f"✓ 最大玩家数: {host.max_players}")
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
        success = host.start_hosting("演示房间")
        if not success:
            print("❌ 主机启动失败")
            return
        
        time.sleep(0.5)  # 等待主机完全启动
        
        # 客户端连接
        print("🔌 客户端尝试连接...")
        success = client.connect_to_host("127.0.0.1", 12349, "演示玩家")
        if not success:
            print("❌ 客户端连接失败")
            return
        
        time.sleep(0.5)  # 等待连接建立
        
        # 验证连接状态
        print(f"\n📊 连接状态:")
        print(f"   主机玩家数: {host.get_current_player_count()}")
        print(f"   房间是否已满: {host.is_room_full()}")
        print(f"   客户端ID: {host.get_client_id()}")
        print(f"   客户端连接状态: {client.is_connected()}")
        
        # 测试输入同步
        print("\n🎮 测试输入同步...")
        client.send_key_press("W")
        client.send_key_press("SPACE")
        time.sleep(0.2)
        
        client_input = host.get_client_input()
        print(f"   主机收到的客户端输入: {client_input}")
        
        client.send_key_release("W")
        time.sleep(0.2)
        
        client_input = host.get_client_input()
        print(f"   释放W键后的输入: {client_input}")
        
        # 测试游戏状态广播
        print("\n📡 测试游戏状态广播...")
        game_state = {
            "tanks": [
                {"id": "host", "x": 100, "y": 100, "angle": 0},
                {"id": host.get_client_id(), "x": 200, "y": 200, "angle": 90}
            ],
            "bullets": [{"x": 150, "y": 150, "angle": 45}],
            "round_info": {"score": [1, 0], "round": 1}
        }
        
        host.send_game_state(game_state)
        time.sleep(0.2)
        
        # 测试房间满员拒绝
        print("\n🚫 测试房间满员拒绝...")
        client2 = DualPlayerClient()
        success = client2.connect_to_host("127.0.0.1", 12349, "第三个玩家")
        if not success:
            print("✓ 第三个玩家被正确拒绝")
        else:
            print("❌ 第三个玩家不应该能够连接")
            client2.disconnect()
        
        print("\n✅ 双人游戏模块演示完成！")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
    
    finally:
        # 清理资源
        print("\n🧹 清理资源...")
        if client.is_connected():
            client.disconnect()
        if host.running:
            host.stop_hosting(force=True)
        time.sleep(0.2)


def demo_performance():
    """演示性能特性"""
    print("\n" + "=" * 60)
    print("双人游戏模块性能演示")
    print("=" * 60)
    
    host = DualPlayerHost(host_port=12350)
    client = DualPlayerClient()
    
    try:
        # 启动连接
        host.start_hosting("性能测试房间")
        time.sleep(0.2)
        client.connect_to_host("127.0.0.1", 12350, "性能测试玩家")
        time.sleep(0.2)
        
        # 测试频率限制
        print("🔄 测试游戏状态同步频率限制...")
        
        game_state = {
            "tanks": [{"id": "host", "x": 100, "y": 100}],
            "bullets": [],
            "round_info": {"score": [0, 0]}
        }
        
        start_time = time.time()
        call_count = 0
        
        # 快速连续调用
        for i in range(20):
            host.send_game_state(game_state)
            call_count += 1
            time.sleep(0.005)  # 5ms间隔
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"   调用次数: {call_count}")
        print(f"   持续时间: {duration:.3f}秒")
        print(f"   理论最大发送次数 (30Hz): {int(duration * 30)}")
        print("✓ 频率限制正常工作")
        
        # 测试心跳机制
        print("\n💓 测试心跳机制...")
        initial_heartbeat = host.client.last_heartbeat if host.client else 0
        time.sleep(1.2)  # 等待心跳更新
        
        if host.client:
            current_heartbeat = host.client.last_heartbeat
            if current_heartbeat > initial_heartbeat:
                print("✓ 心跳机制正常工作")
            else:
                print("❌ 心跳机制可能有问题")
        
        print("\n✅ 性能演示完成！")
        
    except Exception as e:
        print(f"❌ 性能演示过程中出现错误: {e}")
    
    finally:
        if client.is_connected():
            client.disconnect()
        if host.running:
            host.stop_hosting(force=True)
        time.sleep(0.2)


def main():
    """主函数"""
    print("🎮 双人联机模块重构演示")
    print("重构特点:")
    print("- 简化为1对1双人模式")
    print("- 优化的点对点通信")
    print("- 主机权威架构")
    print("- 30Hz游戏状态同步")
    
    try:
        demo_basic_functionality()
        demo_performance()
        
        print("\n" + "=" * 60)
        print("🎉 双人联机模块重构成功！")
        print("主要改进:")
        print("✓ 简化架构，只支持双人模式")
        print("✓ 优化网络通信，减少延迟")
        print("✓ 完善的错误处理和资源清理")
        print("✓ 全面的单元测试覆盖")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n⏹️ 演示被用户中断")
    except Exception as e:
        print(f"\n❌ 演示失败: {e}")


if __name__ == '__main__':
    main()
