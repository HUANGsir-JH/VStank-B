"""
多人游戏坦克选择功能演示

展示重构后的坦克选择功能的使用方法
"""

import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from multiplayer.udp_messages import MessageFactory, MessageType


def demo_tank_selection_messages():
    """演示坦克选择消息的创建和使用"""
    print("🎮 坦克选择消息演示")
    print("=" * 50)
    
    # 1. 坦克选择消息
    print("\n1. 创建坦克选择消息:")
    tank_msg = MessageFactory.create_tank_selected(
        "player1", "green", "/path/to/green_tank.png"
    )
    print(f"   消息类型: {tank_msg.type}")
    print(f"   玩家ID: {tank_msg.player_id}")
    print(f"   坦克类型: {tank_msg.data['tank_type']}")
    print(f"   坦克图片: {tank_msg.data['tank_image_path']}")
    
    # 2. 坦克选择同步消息
    print("\n2. 创建坦克选择同步消息:")
    selected_tanks = {
        "host": {"tank_type": "green", "tank_image_path": "/path/to/green.png"},
        "client1": {"tank_type": "blue", "tank_image_path": "/path/to/blue.png"}
    }
    ready_players = ["host"]
    
    sync_msg = MessageFactory.create_tank_selection_sync(selected_tanks, ready_players)
    print(f"   消息类型: {sync_msg.type}")
    print(f"   已选择坦克: {len(sync_msg.data['selected_tanks'])} 个")
    print(f"   准备玩家: {len(sync_msg.data['ready_players'])} 个")
    
    # 3. 坦克选择冲突消息
    print("\n3. 创建坦克选择冲突消息:")
    conflict_msg = MessageFactory.create_tank_selection_conflict(
        "player2", "green", "坦克已被其他玩家选择"
    )
    print(f"   消息类型: {conflict_msg.type}")
    print(f"   冲突玩家: {conflict_msg.player_id}")
    print(f"   冲突坦克: {conflict_msg.data['tank_type']}")
    print(f"   冲突原因: {conflict_msg.data['reason']}")
    
    # 4. 坦克选择准备消息
    print("\n4. 创建坦克选择准备消息:")
    ready_msg = MessageFactory.create_tank_selection_ready(
        "player1", "blue", "/path/to/blue.png"
    )
    print(f"   消息类型: {ready_msg.type}")
    print(f"   准备玩家: {ready_msg.player_id}")
    print(f"   选择坦克: {ready_msg.data['tank_type']}")


def demo_tank_selection_workflow():
    """演示完整的坦克选择工作流程"""
    print("\n\n🔄 坦克选择工作流程演示")
    print("=" * 50)
    
    # 模拟主机状态
    host_selected_tanks = {}
    host_ready_players = set()
    host_connected_players = {"host", "client1", "client2"}
    
    print("\n📋 初始状态:")
    print(f"   连接玩家: {list(host_connected_players)}")
    print(f"   已选择坦克: {len(host_selected_tanks)}")
    print(f"   准备玩家: {len(host_ready_players)}")
    
    # 步骤1: 主机选择坦克
    print("\n🎯 步骤1: 主机选择坦克")
    host_selected_tanks["host"] = {
        "tank_type": "green",
        "tank_image_path": "/path/to/green.png"
    }
    print(f"   主机选择: {host_selected_tanks['host']['tank_type']}")
    
    # 步骤2: 客户端1选择坦克
    print("\n🎯 步骤2: 客户端1选择坦克")
    client1_selection = {
        "tank_type": "blue",
        "tank_image_path": "/path/to/blue.png"
    }
    
    # 检查冲突
    tank_types = [info["tank_type"] for info in host_selected_tanks.values()]
    if client1_selection["tank_type"] in tank_types:
        print(f"   ❌ 冲突: {client1_selection['tank_type']} 已被选择")
    else:
        host_selected_tanks["client1"] = client1_selection
        print(f"   ✅ 客户端1选择: {client1_selection['tank_type']}")
    
    # 步骤3: 客户端2尝试选择相同坦克（冲突）
    print("\n🎯 步骤3: 客户端2尝试选择坦克（冲突测试）")
    client2_selection = {
        "tank_type": "green",  # 与主机相同
        "tank_image_path": "/path/to/green.png"
    }
    
    tank_types = [info["tank_type"] for info in host_selected_tanks.values()]
    if client2_selection["tank_type"] in tank_types:
        print(f"   ❌ 冲突: {client2_selection['tank_type']} 已被主机选择")
        print("   💡 建议选择其他坦克")
        
        # 选择替代坦克
        alternative_tanks = ["yellow", "grey"]
        for alt_tank in alternative_tanks:
            if alt_tank not in tank_types:
                client2_selection["tank_type"] = alt_tank
                client2_selection["tank_image_path"] = f"/path/to/{alt_tank}.png"
                host_selected_tanks["client2"] = client2_selection
                print(f"   ✅ 客户端2改选: {alt_tank}")
                break
    
    # 步骤4: 玩家准备
    print("\n🎯 步骤4: 玩家准备确认")
    host_ready_players.add("host")
    print("   ✅ 主机已准备")
    
    host_ready_players.add("client1")
    print("   ✅ 客户端1已准备")
    
    host_ready_players.add("client2")
    print("   ✅ 客户端2已准备")
    
    # 步骤5: 检查所有玩家准备状态
    print("\n🎯 步骤5: 检查准备状态")
    all_ready = len(host_ready_players) >= len(host_connected_players)
    print(f"   准备玩家: {len(host_ready_players)}/{len(host_connected_players)}")
    
    if all_ready:
        print("   🚀 所有玩家已准备，开始游戏！")
    else:
        print("   ⏳ 等待其他玩家准备...")
    
    # 最终状态
    print("\n📊 最终状态:")
    for player_id, tank_info in host_selected_tanks.items():
        ready_status = "✅" if player_id in host_ready_players else "⏳"
        print(f"   {player_id}: {tank_info['tank_type']} {ready_status}")


def demo_message_serialization():
    """演示消息序列化和反序列化"""
    print("\n\n📦 消息序列化演示")
    print("=" * 50)
    
    # 创建一个复杂的同步消息
    selected_tanks = {
        "host": {"tank_type": "green", "tank_image_path": "/path/to/green.png"},
        "client1": {"tank_type": "blue", "tank_image_path": "/path/to/blue.png"},
        "client2": {"tank_type": "yellow", "tank_image_path": "/path/to/yellow.png"}
    }
    ready_players = ["host", "client1"]
    
    original_msg = MessageFactory.create_tank_selection_sync(selected_tanks, ready_players)
    
    print("\n📤 原始消息:")
    print(f"   类型: {original_msg.type}")
    print(f"   数据大小: {len(str(original_msg.data))} 字符")
    
    # 序列化
    serialized = original_msg.to_bytes()
    print(f"\n📦 序列化后:")
    print(f"   字节大小: {len(serialized)} bytes")
    
    # 反序列化
    deserialized = original_msg.from_bytes(serialized)
    print(f"\n📥 反序列化后:")
    print(f"   类型: {deserialized.type}")
    print(f"   选择坦克数: {len(deserialized.data['selected_tanks'])}")
    print(f"   准备玩家数: {len(deserialized.data['ready_players'])}")
    
    # 验证数据完整性
    data_match = (
        deserialized.type == original_msg.type and
        deserialized.data == original_msg.data
    )
    print(f"\n✅ 数据完整性: {'通过' if data_match else '失败'}")


def main():
    """主演示函数"""
    print("🎮 多人游戏坦克选择功能演示")
    print("🔧 重构后的网络同步坦克选择系统")
    print("=" * 60)
    
    try:
        # 演示消息创建
        demo_tank_selection_messages()
        
        # 演示工作流程
        demo_tank_selection_workflow()
        
        # 演示消息序列化
        demo_message_serialization()
        
        print("\n\n🎉 演示完成！")
        print("=" * 60)
        print("📋 重构要点:")
        print("   ✅ 专门的坦克选择视图 (NetworkTankSelectionView)")
        print("   ✅ 网络同步的坦克选择状态")
        print("   ✅ 坦克选择冲突检测和处理")
        print("   ✅ 实时准备状态同步")
        print("   ✅ 完整的消息协议支持")
        
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
