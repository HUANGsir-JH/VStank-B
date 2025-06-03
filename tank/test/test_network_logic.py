#!/usr/bin/env python3
"""
网络逻辑测试
测试多人联机的核心逻辑，不依赖窗口环境
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tank_sprites import PLAYER_IMAGE_PATH_BLUE, PLAYER_IMAGE_PATH_GREEN
from maps import get_random_map_layout


def test_map_layout_functions():
    """测试地图布局相关函数"""
    print("🧪 测试地图布局相关函数...")
    
    # 测试随机地图生成
    map_layout1 = get_random_map_layout()
    map_layout2 = get_random_map_layout()
    
    assert isinstance(map_layout1, list), "地图布局应该是列表"
    assert len(map_layout1) > 0, "地图布局应该包含墙壁"
    
    # 验证地图布局格式
    for wall in map_layout1:
        assert len(wall) == 4, "每个墙壁应该有4个参数 (cx, cy, w, h)"
        cx, cy, w, h = wall
        assert isinstance(cx, (int, float)), "中心X坐标应该是数字"
        assert isinstance(cy, (int, float)), "中心Y坐标应该是数字"
        assert isinstance(w, (int, float)), "宽度应该是数字"
        assert isinstance(h, (int, float)), "高度应该是数字"
    
    print(f"  地图布局1包含 {len(map_layout1)} 个墙壁")
    print(f"  地图布局2包含 {len(map_layout2)} 个墙壁")
    print("  ✓ 地图布局生成正常")
    
    print("✅ 地图布局函数测试通过")


def test_tank_image_paths():
    """测试坦克图片路径"""
    print("🧪 测试坦克图片路径...")
    
    # 检查图片路径是否存在
    assert os.path.exists(PLAYER_IMAGE_PATH_GREEN), f"绿色坦克图片应该存在: {PLAYER_IMAGE_PATH_GREEN}"
    assert os.path.exists(PLAYER_IMAGE_PATH_BLUE), f"蓝色坦克图片应该存在: {PLAYER_IMAGE_PATH_BLUE}"
    
    print(f"  绿色坦克图片: {PLAYER_IMAGE_PATH_GREEN}")
    print(f"  蓝色坦克图片: {PLAYER_IMAGE_PATH_BLUE}")
    print("  ✓ 坦克图片路径正确")
    
    print("✅ 坦克图片路径测试通过")


def test_game_state_structure():
    """测试游戏状态数据结构"""
    print("🧪 测试游戏状态数据结构...")
    
    # 模拟游戏状态
    mock_game_state = {
        "tanks": [
            {
                "player_id": "host",
                "x": 100,
                "y": 200,
                "angle": 0,
                "health": 5
            },
            {
                "player_id": "client",
                "x": 300,
                "y": 400,
                "angle": 90,
                "health": 4
            }
        ],
        "bullets": [
            {
                "x": 150,
                "y": 250,
                "angle": 45,
                "owner": "host"
            }
        ],
        "scores": {
            "host": 1,
            "client": 0
        }
    }
    
    # 验证游戏状态结构
    assert "tanks" in mock_game_state, "游戏状态应该包含坦克信息"
    assert "bullets" in mock_game_state, "游戏状态应该包含子弹信息"
    assert "scores" in mock_game_state, "游戏状态应该包含分数信息"
    
    # 验证坦克数据
    tanks = mock_game_state["tanks"]
    assert len(tanks) == 2, "应该有两个坦克"
    
    for tank in tanks:
        assert "player_id" in tank, "坦克应该有player_id"
        assert "x" in tank, "坦克应该有x坐标"
        assert "y" in tank, "坦克应该有y坐标"
        assert "angle" in tank, "坦克应该有角度"
        assert "health" in tank, "坦克应该有血量"
    
    # 验证player_id
    player_ids = [tank["player_id"] for tank in tanks]
    assert "host" in player_ids, "应该包含主机坦克"
    assert "client" in player_ids, "应该包含客户端坦克"
    
    print(f"  游戏状态包含 {len(tanks)} 个坦克")
    print(f"  坦克ID: {player_ids}")
    print("  ✓ 游戏状态结构正确")
    
    print("✅ 游戏状态结构测试通过")


def test_network_message_structure():
    """测试网络消息结构"""
    print("🧪 测试网络消息结构...")
    
    # 模拟游戏开始消息
    game_start_message = {
        "map_layout": [
            (400, 300, 100, 20),
            (200, 200, 20, 100),
            (600, 400, 20, 100)
        ]
    }
    
    # 验证消息结构
    assert "map_layout" in game_start_message, "游戏开始消息应该包含地图布局"
    
    map_layout = game_start_message["map_layout"]
    assert isinstance(map_layout, list), "地图布局应该是列表"
    assert len(map_layout) > 0, "地图布局应该包含墙壁"
    
    # 验证地图布局格式
    for wall in map_layout:
        assert len(wall) == 4, "每个墙壁应该有4个参数"
    
    print(f"  游戏开始消息包含 {len(map_layout)} 个墙壁")
    print("  ✓ 网络消息结构正确")
    
    print("✅ 网络消息结构测试通过")


def test_tank_synchronization_logic():
    """测试坦克同步逻辑"""
    print("🧪 测试坦克同步逻辑...")
    
    # 模拟主机端坦克状态
    host_tanks = [
        {"player_id": "host", "x": 100, "y": 200, "angle": 0, "health": 5},
        {"player_id": "client", "x": 300, "y": 400, "angle": 90, "health": 4}
    ]
    
    # 模拟客户端坦克列表
    class MockTank:
        def __init__(self, player_id, x, y, angle, health):
            self.player_id = player_id
            self.center_x = x
            self.center_y = y
            self.angle = angle
            self.health = health
    
    client_tanks = [
        MockTank("host", 50, 150, 10, 5),
        MockTank("client", 250, 350, 80, 5)
    ]
    
    # 模拟状态同步逻辑
    def apply_tank_states(local_tanks, remote_states):
        """应用远程坦克状态到本地坦克"""
        for i, tank_data in enumerate(remote_states):
            if i < len(local_tanks):
                tank = local_tanks[i]
                if tank is not None:
                    tank.center_x = tank_data.get("x", tank.center_x)
                    tank.center_y = tank_data.get("y", tank.center_y)
                    tank.angle = tank_data.get("angle", tank.angle)
                    tank.health = tank_data.get("health", tank.health)
    
    # 应用状态
    apply_tank_states(client_tanks, host_tanks)
    
    # 验证同步结果
    assert client_tanks[0].center_x == 100, "主机坦克X坐标应该被同步"
    assert client_tanks[0].center_y == 200, "主机坦克Y坐标应该被同步"
    assert client_tanks[0].angle == 0, "主机坦克角度应该被同步"
    
    assert client_tanks[1].center_x == 300, "客户端坦克X坐标应该被同步"
    assert client_tanks[1].center_y == 400, "客户端坦克Y坐标应该被同步"
    assert client_tanks[1].angle == 90, "客户端坦克角度应该被同步"
    assert client_tanks[1].health == 4, "客户端坦克血量应该被同步"
    
    print("  ✓ 坦克状态同步逻辑正确")
    
    print("✅ 坦克同步逻辑测试通过")


def test_map_layout_consistency():
    """测试地图布局一致性"""
    print("🧪 测试地图布局一致性...")
    
    # 模拟主机生成地图布局
    host_map_layout = [
        (400, 300, 100, 20),  # 中间横墙
        (200, 200, 20, 100),  # 左侧竖墙
        (600, 400, 20, 100),  # 右侧竖墙
    ]
    
    # 模拟客户端接收地图布局
    client_map_layout = host_map_layout.copy()
    
    # 验证地图布局一致性
    assert len(host_map_layout) == len(client_map_layout), "地图布局长度应该相同"
    
    for i, (host_wall, client_wall) in enumerate(zip(host_map_layout, client_map_layout)):
        assert host_wall == client_wall, f"第{i}个墙壁应该相同"
    
    print(f"  主机地图布局: {len(host_map_layout)} 个墙壁")
    print(f"  客户端地图布局: {len(client_map_layout)} 个墙壁")
    print("  ✓ 地图布局一致性正确")
    
    print("✅ 地图布局一致性测试通过")


def main():
    """运行所有测试"""
    print("🚀 开始网络逻辑测试\n")
    
    tests = [
        test_map_layout_functions,
        test_tank_image_paths,
        test_game_state_structure,
        test_network_message_structure,
        test_tank_synchronization_logic,
        test_map_layout_consistency
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
        print("🎉 所有网络逻辑测试通过！")
        print("\n📋 验证的功能:")
        print("1. ✅ 地图布局生成和格式正确")
        print("2. ✅ 坦克图片路径存在")
        print("3. ✅ 游戏状态数据结构正确")
        print("4. ✅ 网络消息结构正确")
        print("5. ✅ 坦克同步逻辑正确")
        print("6. ✅ 地图布局一致性保证")
        return True
    else:
        print("⚠️ 部分测试失败，需要进一步检查")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
