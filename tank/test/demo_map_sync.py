"""
地图同步功能演示
展示地图同步的完整流程和功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multiplayer.map_sync import MapSyncManager
from multiplayer.messages import MessageFactory, MessageType
from maps import get_random_map_layout, MAP_1_WALLS, MAP_2_WALLS, MAP_3_WALLS


def print_separator(title):
    """打印分隔符"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_map_info(map_layout, title="地图信息"):
    """打印地图信息"""
    info = MapSyncManager.get_map_info(map_layout)
    print(f"\n📊 {title}:")
    print(f"  墙壁数量: {info['wall_count']}")
    print(f"  地图边界: X({info['bounds']['min_x']:.1f} - {info['bounds']['max_x']:.1f}), Y({info['bounds']['min_y']:.1f} - {info['bounds']['max_y']:.1f})")
    print(f"  总墙壁面积: {info['total_wall_area']}")
    print(f"  校验和: {info['checksum'][:16]}...")


def demo_basic_map_sync():
    """演示基本地图同步功能"""
    print_separator("基本地图同步演示")
    
    print("🎯 演示目标: 展示地图数据的序列化、传输和反序列化过程")
    
    # 选择一个地图
    map_layout = MAP_1_WALLS
    print_map_info(map_layout, "原始地图")
    
    print("\n🔄 步骤1: 序列化地图数据")
    serialized = MapSyncManager.serialize_map_data(map_layout)
    print(f"  序列化成功: {len(str(serialized))} 字符")
    print(f"  包含字段: {list(serialized.keys())}")
    
    print("\n🔄 步骤2: 创建网络消息")
    message = MessageFactory.create_map_sync(map_layout, serialized['checksum'])
    print(f"  消息类型: {message.type.value}")
    print(f"  消息大小: {len(message.to_bytes())} 字节")
    
    print("\n🔄 步骤3: 模拟网络传输")
    msg_bytes = message.to_bytes()
    received_msg = message.from_bytes(msg_bytes)
    print(f"  传输成功: {received_msg.type.value}")
    
    print("\n🔄 步骤4: 反序列化地图数据")
    received_map = received_msg.data["map_layout"]
    print_map_info(received_map, "接收到的地图")
    
    print("\n🔄 步骤5: 验证地图一致性")
    is_same = MapSyncManager.compare_maps(map_layout, received_map)
    print(f"  地图一致性: {'✅ 完全一致' if is_same else '❌ 不一致'}")


def demo_multiple_maps():
    """演示多种地图的同步"""
    print_separator("多种地图同步演示")
    
    print("🎯 演示目标: 展示不同地图的同步效果")
    
    maps = [
        ("地图1 - 横向障碍", MAP_1_WALLS),
        ("地图2 - H型障碍", MAP_2_WALLS),
        ("地图3 - 十字障碍", MAP_3_WALLS),
        ("随机地图", get_random_map_layout())
    ]
    
    for map_name, map_layout in maps:
        print(f"\n🗺️ {map_name}")
        
        # 序列化
        serialized = MapSyncManager.serialize_map_data(map_layout)
        
        # 创建消息
        message = MessageFactory.create_map_sync(map_layout, serialized['checksum'])
        
        # 传输
        msg_bytes = message.to_bytes()
        received_msg = message.from_bytes(msg_bytes)
        received_map = received_msg.data["map_layout"]
        
        # 验证
        is_same = MapSyncManager.compare_maps(map_layout, received_map)
        
        print(f"  墙壁数量: {len(map_layout)}")
        print(f"  消息大小: {len(msg_bytes)} 字节")
        print(f"  同步结果: {'✅ 成功' if is_same else '❌ 失败'}")


def demo_error_handling():
    """演示错误处理"""
    print_separator("错误处理演示")
    
    print("🎯 演示目标: 展示各种错误情况的处理")
    
    print("\n❌ 测试1: 无效地图数据")
    invalid_maps = [
        ("空地图", []),
        ("参数不足", [(100, 200)]),
        ("负尺寸", [(100, 200, -50, 30)]),
        ("非数字坐标", [("a", 200, 50, 30)])
    ]
    
    for error_name, invalid_map in invalid_maps:
        try:
            MapSyncManager.serialize_map_data(invalid_map)
            print(f"  {error_name}: ❌ 应该被拒绝但通过了")
        except ValueError as e:
            print(f"  {error_name}: ✅ 正确拒绝 - {str(e)[:50]}...")
    
    print("\n❌ 测试2: 校验和错误")
    valid_map = [(100, 200, 50, 30)]
    serialized = MapSyncManager.serialize_map_data(valid_map)
    
    # 修改校验和
    serialized['checksum'] = 'invalid_checksum'
    
    try:
        MapSyncManager.deserialize_map_data(serialized)
        print("  校验和错误: ❌ 应该被检测但通过了")
    except ValueError as e:
        print(f"  校验和错误: ✅ 正确检测 - {str(e)[:50]}...")


def demo_performance():
    """演示性能特性"""
    print_separator("性能特性演示")
    
    print("🎯 演示目标: 展示不同大小地图的性能表现")
    
    import time
    
    # 创建不同大小的地图
    test_maps = []
    
    # 小地图
    small_map = [(100, 200, 50, 30)]
    test_maps.append(("小地图 (1个墙壁)", small_map))
    
    # 中等地图
    medium_map = MAP_1_WALLS
    test_maps.append(("中等地图 (8个墙壁)", medium_map))
    
    # 大地图
    large_map = []
    for x in range(100, 800, 100):
        for y in range(100, 500, 100):
            large_map.append((x, y, 50, 30))
    test_maps.append((f"大地图 ({len(large_map)}个墙壁)", large_map))
    
    for map_name, map_layout in test_maps:
        print(f"\n📊 {map_name}")
        
        # 测试序列化时间
        start_time = time.time()
        serialized = MapSyncManager.serialize_map_data(map_layout)
        serialize_time = (time.time() - start_time) * 1000
        
        # 测试消息创建时间
        start_time = time.time()
        message = MessageFactory.create_map_sync(map_layout, serialized['checksum'])
        msg_bytes = message.to_bytes()
        message_time = (time.time() - start_time) * 1000
        
        # 测试反序列化时间
        start_time = time.time()
        received_msg = message.from_bytes(msg_bytes)
        received_map = received_msg.data["map_layout"]
        deserialize_time = (time.time() - start_time) * 1000
        
        print(f"  序列化时间: {serialize_time:.2f} ms")
        print(f"  消息创建时间: {message_time:.2f} ms")
        print(f"  反序列化时间: {deserialize_time:.2f} ms")
        print(f"  消息大小: {len(msg_bytes)} 字节")
        
        if len(msg_bytes) > 8192:
            print(f"  ⚠️ 警告: 消息大小超过UDP限制 ({len(msg_bytes)} > 8192)")


def demo_real_world_scenario():
    """演示真实世界场景"""
    print_separator("真实场景演示")
    
    print("🎯 演示目标: 模拟完整的主机-客户端地图同步流程")
    
    print("\n🖥️ 主机端操作:")
    
    # 主机生成地图
    print("  1. 生成随机地图...")
    host_map = get_random_map_layout()
    print_map_info(host_map, "主机地图")
    
    # 主机验证地图
    print("\n  2. 验证地图数据...")
    if MapSyncManager.validate_map_layout(host_map):
        print("     ✅ 地图数据有效")
    else:
        print("     ❌ 地图数据无效，使用默认地图")
        host_map = MAP_1_WALLS
    
    # 主机序列化地图
    print("\n  3. 序列化地图数据...")
    host_serialized = MapSyncManager.serialize_map_data(host_map)
    print(f"     序列化完成: {host_serialized['wall_count']} 个墙壁")
    print(f"     校验和: {host_serialized['checksum'][:16]}...")
    
    # 主机发送消息
    print("\n  4. 创建并发送地图同步消息...")
    map_sync_msg = MessageFactory.create_map_sync(host_map, host_serialized['checksum'])
    game_start_msg = MessageFactory.create_game_start({
        "map_layout": host_map,
        "map_checksum": host_serialized['checksum']
    })
    
    print(f"     MAP_SYNC 消息: {len(map_sync_msg.to_bytes())} 字节")
    print(f"     GAME_START 消息: {len(game_start_msg.to_bytes())} 字节")
    
    print("\n📱 客户端操作:")
    
    # 客户端接收MAP_SYNC
    print("  1. 接收MAP_SYNC消息...")
    received_sync = map_sync_msg.from_bytes(map_sync_msg.to_bytes())
    client_map_from_sync = received_sync.data["map_layout"]
    client_checksum_from_sync = received_sync.data.get("map_checksum")
    
    # 客户端验证MAP_SYNC
    print("  2. 验证MAP_SYNC数据...")
    if MapSyncManager.validate_map_layout(client_map_from_sync):
        print("     ✅ 地图数据格式有效")
    else:
        print("     ❌ 地图数据格式无效")
        return
    
    if client_checksum_from_sync:
        actual_checksum = MapSyncManager.calculate_map_checksum(client_map_from_sync)
        if actual_checksum == client_checksum_from_sync:
            print("     ✅ 校验和验证通过")
        else:
            print("     ❌ 校验和验证失败")
            return
    
    # 客户端接收GAME_START
    print("\n  3. 接收GAME_START消息...")
    received_start = game_start_msg.from_bytes(game_start_msg.to_bytes())
    client_map_from_start = received_start.data["map_layout"]
    
    # 客户端验证一致性
    print("  4. 验证地图一致性...")
    sync_vs_start = MapSyncManager.compare_maps(client_map_from_sync, client_map_from_start)
    host_vs_client = MapSyncManager.compare_maps(host_map, client_map_from_sync)
    
    print(f"     MAP_SYNC vs GAME_START: {'✅ 一致' if sync_vs_start else '❌ 不一致'}")
    print(f"     主机 vs 客户端: {'✅ 一致' if host_vs_client else '❌ 不一致'}")
    
    if sync_vs_start and host_vs_client:
        print("\n🎉 地图同步成功！主机和客户端将显示相同的地图")
    else:
        print("\n❌ 地图同步失败！需要检查同步机制")


def main():
    """主演示函数"""
    print("🚀 地图同步功能演示")
    print("本演示将展示多人联机对战中地图同步的完整功能")
    
    demos = [
        demo_basic_map_sync,
        demo_multiple_maps,
        demo_error_handling,
        demo_performance,
        demo_real_world_scenario
    ]
    
    for i, demo in enumerate(demos, 1):
        try:
            demo()
            if i < len(demos):
                input(f"\n按回车键继续下一个演示 ({i+1}/{len(demos)})...")
        except KeyboardInterrupt:
            print("\n\n演示被用户中断")
            break
        except Exception as e:
            print(f"\n❌ 演示出错: {e}")
            import traceback
            traceback.print_exc()
    
    print_separator("演示结束")
    print("🎉 地图同步功能演示完成！")
    print("现在多人联机对战中的地图将完全同步，确保公平的游戏体验。")


if __name__ == "__main__":
    main()
