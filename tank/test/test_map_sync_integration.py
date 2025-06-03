"""
地图同步集成测试
测试完整的地图同步流程，包括主机端生成、客户端接收和验证
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multiplayer.map_sync import MapSyncManager
from multiplayer.messages import MessageFactory, MessageType, NetworkMessage
from maps import get_random_map_layout, MAP_1_WALLS


def test_host_client_map_sync():
    """测试主机-客户端地图同步流程"""
    print("🧪 测试主机-客户端地图同步流程...")
    
    # 模拟主机端
    print("  📡 主机端: 生成地图...")
    host_map_layout = get_random_map_layout()
    
    # 主机端验证和序列化地图
    if not MapSyncManager.validate_map_layout(host_map_layout):
        print("❌ 主机端地图验证失败")
        return False
    
    host_map_data = MapSyncManager.serialize_map_data(host_map_layout)
    print(f"  ✅ 主机端地图序列化: {host_map_data['wall_count']} 个墙壁, 校验和: {host_map_data['checksum'][:8]}...")
    
    # 主机端创建地图同步消息
    map_sync_msg = MessageFactory.create_map_sync(
        host_map_layout, 
        host_map_data['checksum']
    )
    
    # 模拟网络传输
    print("  🌐 网络传输: 序列化消息...")
    msg_bytes = map_sync_msg.to_bytes()
    
    # 模拟客户端接收
    print("  📱 客户端: 接收消息...")
    received_msg = NetworkMessage.from_bytes(msg_bytes)
    
    # 验证消息类型
    if received_msg.type != MessageType.MAP_SYNC:
        print("❌ 消息类型错误")
        return False
    
    # 客户端处理地图数据
    print("  📱 客户端: 处理地图数据...")
    client_map_layout = received_msg.data["map_layout"]
    client_map_checksum = received_msg.data.get("map_checksum")
    
    # 客户端验证地图数据
    if not MapSyncManager.validate_map_layout(client_map_layout):
        print("❌ 客户端地图验证失败")
        return False
    
    # 验证校验和
    if client_map_checksum:
        actual_checksum = MapSyncManager.calculate_map_checksum(client_map_layout)
        if actual_checksum != client_map_checksum:
            print(f"❌ 校验和不匹配: 期望 {client_map_checksum[:8]}..., 实际 {actual_checksum[:8]}...")
            return False
        print(f"  ✅ 客户端校验和验证通过: {actual_checksum[:8]}...")
    
    # 比较主机和客户端地图
    if MapSyncManager.compare_maps(host_map_layout, client_map_layout):
        print("  ✅ 主机-客户端地图同步成功")
        return True
    else:
        print("❌ 主机-客户端地图不匹配")
        return False


def test_game_start_with_map():
    """测试游戏开始消息包含地图数据"""
    print("🧪 测试游戏开始消息包含地图数据...")
    
    # 生成地图
    map_layout = MAP_1_WALLS
    map_checksum = MapSyncManager.calculate_map_checksum(map_layout)
    
    # 创建游戏开始消息
    game_start_msg = MessageFactory.create_game_start({
        "map_layout": map_layout,
        "map_checksum": map_checksum
    })
    
    # 序列化和反序列化
    msg_bytes = game_start_msg.to_bytes()
    received_msg = NetworkMessage.from_bytes(msg_bytes)
    
    # 验证消息
    if received_msg.type != MessageType.GAME_START:
        print("❌ 消息类型错误")
        return False
    
    if "map_layout" not in received_msg.data:
        print("❌ 游戏开始消息缺少地图布局")
        return False
    
    if "map_checksum" not in received_msg.data:
        print("❌ 游戏开始消息缺少地图校验和")
        return False
    
    # 验证地图数据
    received_map = received_msg.data["map_layout"]
    received_checksum = received_msg.data["map_checksum"]
    
    if not MapSyncManager.compare_maps(map_layout, received_map):
        print("❌ 地图数据不匹配")
        return False
    
    actual_checksum = MapSyncManager.calculate_map_checksum(received_map)
    if actual_checksum != received_checksum:
        print("❌ 校验和不匹配")
        return False
    
    print(f"  ✅ 游戏开始消息地图同步成功: {len(received_map)} 个墙壁")
    return True


def test_multiple_map_sync():
    """测试多次地图同步"""
    print("🧪 测试多次地图同步...")
    
    success_count = 0
    total_tests = 5
    
    for i in range(total_tests):
        print(f"  测试轮次 {i+1}/{total_tests}...")
        
        # 生成不同的地图
        map_layout = get_random_map_layout()
        
        # 序列化
        map_data = MapSyncManager.serialize_map_data(map_layout)
        
        # 创建消息
        msg = MessageFactory.create_map_sync(
            map_layout, 
            map_data['checksum']
        )
        
        # 传输
        msg_bytes = msg.to_bytes()
        received_msg = NetworkMessage.from_bytes(msg_bytes)
        
        # 验证
        received_map = received_msg.data["map_layout"]
        if MapSyncManager.compare_maps(map_layout, received_map):
            success_count += 1
            print(f"    ✅ 轮次 {i+1} 成功")
        else:
            print(f"    ❌ 轮次 {i+1} 失败")
    
    print(f"  📊 多次同步结果: {success_count}/{total_tests} 成功")
    return success_count == total_tests


def test_large_map_sync():
    """测试大地图同步"""
    print("🧪 测试大地图同步...")
    
    # 创建一个包含很多墙壁的大地图
    large_map = []
    for x in range(100, 1000, 100):
        for y in range(100, 600, 100):
            large_map.append((x, y, 50, 30))
    
    print(f"  📏 大地图包含 {len(large_map)} 个墙壁")
    
    # 验证大地图
    if not MapSyncManager.validate_map_layout(large_map):
        print("❌ 大地图验证失败")
        return False
    
    # 序列化大地图
    try:
        map_data = MapSyncManager.serialize_map_data(large_map)
        print(f"  ✅ 大地图序列化成功: {map_data['wall_count']} 个墙壁")
    except Exception as e:
        print(f"❌ 大地图序列化失败: {e}")
        return False
    
    # 创建消息
    msg = MessageFactory.create_map_sync(large_map, map_data['checksum'])
    
    # 测试消息大小
    msg_bytes = msg.to_bytes()
    msg_size = len(msg_bytes)
    print(f"  📦 消息大小: {msg_size} 字节")
    
    if msg_size > 8192:  # UDP包大小限制
        print(f"⚠️ 消息大小超过UDP限制 ({msg_size} > 8192 字节)")
        print("  建议: 对于大地图，考虑分块传输或压缩")
    
    # 传输和验证
    try:
        received_msg = NetworkMessage.from_bytes(msg_bytes)
        received_map = received_msg.data["map_layout"]
        
        if MapSyncManager.compare_maps(large_map, received_map):
            print("  ✅ 大地图同步成功")
            return True
        else:
            print("❌ 大地图同步失败")
            return False
    except Exception as e:
        print(f"❌ 大地图传输失败: {e}")
        return False


def test_error_recovery():
    """测试错误恢复"""
    print("🧪 测试错误恢复...")
    
    # 测试损坏的地图数据
    corrupted_map = [(100, 200, 50, 30), (300, 400, -80, 40)]  # 负宽度
    
    try:
        MapSyncManager.serialize_map_data(corrupted_map)
        print("❌ 应该拒绝损坏的地图数据")
        return False
    except ValueError:
        print("  ✅ 正确拒绝损坏的地图数据")
    
    # 测试校验和错误
    valid_map = [(100, 200, 50, 30)]
    map_data = MapSyncManager.serialize_map_data(valid_map)
    
    # 修改校验和
    map_data['checksum'] = 'invalid_checksum'
    
    try:
        MapSyncManager.deserialize_map_data(map_data)
        print("❌ 应该检测到校验和错误")
        return False
    except ValueError:
        print("  ✅ 正确检测到校验和错误")
    
    print("  ✅ 错误恢复测试通过")
    return True


def main():
    """主测试函数"""
    print("🚀 开始地图同步集成测试\n")
    
    tests = [
        ("主机-客户端地图同步", test_host_client_map_sync),
        ("游戏开始消息地图同步", test_game_start_with_map),
        ("多次地图同步", test_multiple_map_sync),
        ("大地图同步", test_large_map_sync),
        ("错误恢复", test_error_recovery)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"🔍 {test_name}...")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 通过\n")
            else:
                print(f"❌ {test_name} 失败\n")
        except Exception as e:
            print(f"❌ {test_name} 出现异常: {e}\n")
            import traceback
            traceback.print_exc()
    
    print("=" * 50)
    print(f"📊 集成测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有集成测试通过！地图同步系统完全正常")
        return True
    else:
        print("⚠️ 部分集成测试失败，需要进一步检查")
        return False


if __name__ == "__main__":
    main()
