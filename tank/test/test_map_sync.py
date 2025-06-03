"""
地图同步功能测试
测试地图数据的序列化、传输和同步机制
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multiplayer.map_sync import MapSyncManager
from multiplayer.messages import MessageFactory, MessageType
from maps import get_random_map_layout, MAP_1_WALLS, MAP_2_WALLS, MAP_3_WALLS


def test_map_sync_manager():
    """测试地图同步管理器"""
    print("🧪 测试地图同步管理器...")
    
    # 测试地图数据
    test_map = [
        (100, 200, 50, 30),  # cx, cy, w, h
        (300, 400, 80, 40),
        (500, 300, 60, 60)
    ]
    
    # 测试验证功能
    assert MapSyncManager.validate_map_layout(test_map), "地图验证失败"
    print("  ✅ 地图验证通过")
    
    # 测试校验和计算
    checksum1 = MapSyncManager.calculate_map_checksum(test_map)
    checksum2 = MapSyncManager.calculate_map_checksum(test_map)
    assert checksum1 == checksum2, "校验和不一致"
    print(f"  ✅ 校验和计算: {checksum1[:8]}...")
    
    # 测试序列化
    serialized = MapSyncManager.serialize_map_data(test_map)
    assert "map_layout" in serialized, "序列化缺少地图布局"
    assert "checksum" in serialized, "序列化缺少校验和"
    assert "wall_count" in serialized, "序列化缺少墙壁数量"
    print("  ✅ 地图序列化成功")
    
    # 测试反序列化
    deserialized = MapSyncManager.deserialize_map_data(serialized)
    assert len(deserialized) == len(test_map), "反序列化墙壁数量不匹配"
    print("  ✅ 地图反序列化成功")
    
    # 测试地图比较
    is_same = MapSyncManager.compare_maps(test_map, deserialized)
    assert is_same, "地图比较失败"
    print("  ✅ 地图比较成功")
    
    # 测试地图信息
    map_info = MapSyncManager.get_map_info(test_map)
    assert map_info["valid"], "地图信息无效"
    assert map_info["wall_count"] == len(test_map), "墙壁数量不匹配"
    print("  ✅ 地图信息获取成功")
    
    print("✅ 地图同步管理器测试完成")


def test_predefined_maps():
    """测试预定义地图"""
    print("🧪 测试预定义地图...")
    
    maps_to_test = [
        ("MAP_1_WALLS", MAP_1_WALLS),
        ("MAP_2_WALLS", MAP_2_WALLS),
        ("MAP_3_WALLS", MAP_3_WALLS)
    ]
    
    for map_name, map_layout in maps_to_test:
        print(f"  测试 {map_name}...")
        
        # 验证地图
        assert MapSyncManager.validate_map_layout(map_layout), f"{map_name} 验证失败"
        
        # 序列化和反序列化
        serialized = MapSyncManager.serialize_map_data(map_layout)
        deserialized = MapSyncManager.deserialize_map_data(serialized)
        
        # 比较
        assert MapSyncManager.compare_maps(map_layout, deserialized), f"{map_name} 比较失败"
        
        # 获取信息
        map_info = MapSyncManager.get_map_info(map_layout)
        print(f"    {map_name}: {map_info['wall_count']} 个墙壁, 校验和: {map_info['checksum'][:8]}...")
    
    print("✅ 预定义地图测试完成")


def test_random_maps():
    """测试随机地图"""
    print("🧪 测试随机地图...")
    
    for i in range(5):
        print(f"  测试随机地图 {i+1}...")
        
        # 生成随机地图
        map_layout = get_random_map_layout()
        
        # 验证地图
        assert MapSyncManager.validate_map_layout(map_layout), f"随机地图 {i+1} 验证失败"
        
        # 序列化和反序列化
        serialized = MapSyncManager.serialize_map_data(map_layout)
        deserialized = MapSyncManager.deserialize_map_data(serialized)
        
        # 比较
        assert MapSyncManager.compare_maps(map_layout, deserialized), f"随机地图 {i+1} 比较失败"
        
        # 获取信息
        map_info = MapSyncManager.get_map_info(map_layout)
        print(f"    随机地图 {i+1}: {map_info['wall_count']} 个墙壁, 校验和: {map_info['checksum'][:8]}...")
    
    print("✅ 随机地图测试完成")


def test_message_creation():
    """测试消息创建"""
    print("🧪 测试地图同步消息创建...")
    
    # 创建测试地图
    test_map = MAP_1_WALLS
    checksum = MapSyncManager.calculate_map_checksum(test_map)
    
    # 创建地图同步消息
    map_sync_msg = MessageFactory.create_map_sync(test_map, checksum)
    
    # 验证消息
    assert map_sync_msg.type == MessageType.MAP_SYNC, "消息类型错误"
    assert "map_layout" in map_sync_msg.data, "消息缺少地图布局"
    assert "map_checksum" in map_sync_msg.data, "消息缺少校验和"
    assert "wall_count" in map_sync_msg.data, "消息缺少墙壁数量"
    
    print(f"  ✅ 地图同步消息创建成功: {map_sync_msg.data['wall_count']} 个墙壁")
    
    # 测试消息序列化和反序列化
    msg_bytes = map_sync_msg.to_bytes()
    restored_msg = map_sync_msg.from_bytes(msg_bytes)
    
    assert restored_msg.type == MessageType.MAP_SYNC, "消息类型恢复错误"
    assert restored_msg.data["wall_count"] == len(test_map), "墙壁数量恢复错误"
    
    print("  ✅ 消息序列化和反序列化成功")
    
    print("✅ 地图同步消息测试完成")


def test_error_handling():
    """测试错误处理"""
    print("🧪 测试错误处理...")
    
    # 测试无效地图数据
    invalid_maps = [
        [],  # 空地图
        [(100, 200)],  # 参数不足
        [(100, 200, 50, 30, 40)],  # 参数过多
        [(100, 200, -50, 30)],  # 负宽度
        [(100, 200, 50, -30)],  # 负高度
        [("a", 200, 50, 30)],  # 非数字坐标
    ]
    
    for i, invalid_map in enumerate(invalid_maps):
        try:
            result = MapSyncManager.validate_map_layout(invalid_map)
            assert not result, f"无效地图 {i+1} 应该验证失败"
            print(f"  ✅ 无效地图 {i+1} 正确被拒绝")
        except Exception as e:
            print(f"  ✅ 无效地图 {i+1} 抛出异常: {e}")
    
    # 测试校验和不匹配
    test_map = [(100, 200, 50, 30)]
    serialized = MapSyncManager.serialize_map_data(test_map)
    
    # 修改校验和
    serialized["checksum"] = "invalid_checksum"
    
    try:
        MapSyncManager.deserialize_map_data(serialized)
        assert False, "应该抛出校验和错误"
    except ValueError as e:
        assert "校验失败" in str(e), "错误信息不正确"
        print("  ✅ 校验和不匹配正确被检测")
    
    print("✅ 错误处理测试完成")


def main():
    """主测试函数"""
    print("🚀 开始地图同步功能测试\n")
    
    tests = [
        test_map_sync_manager,
        test_predefined_maps,
        test_random_maps,
        test_message_creation,
        test_error_handling
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            test()
            passed += 1
            print()
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            print()
    
    print("=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！地图同步功能正常")
    else:
        print("⚠️ 部分测试失败，需要进一步检查")


if __name__ == "__main__":
    main()
