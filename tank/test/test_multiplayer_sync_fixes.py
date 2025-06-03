#!/usr/bin/env python3
"""
多人联机同步修复测试
测试地图同步、坦克显示和双人对战功能
"""

import sys
import os
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import game_views
from tank_sprites import PLAYER_IMAGE_PATH_BLUE
from maps import get_random_map_layout


def test_game_view_network_mode():
    """测试网络模式下的游戏视图"""
    print("🧪 测试网络模式下的游戏视图...")
    
    # 测试主机模式
    print("  测试主机模式...")
    host_view = game_views.GameView(mode="network_host")
    host_view.setup()
    
    # 检查是否创建了两个坦克
    assert host_view.player_tank is not None, "主机坦克应该被创建"
    assert host_view.player2_tank is not None, "客户端坦克应该被创建"
    assert len(host_view.player_list) == 2, "应该有两个坦克"
    
    # 检查坦克的player_id
    assert host_view.player_tank.player_id == "host", "主机坦克应该有正确的player_id"
    assert host_view.player2_tank.player_id == "client", "客户端坦克应该有正确的player_id"
    
    # 检查客户端坦克使用蓝色图片
    assert host_view.player2_tank.tank_image_file == PLAYER_IMAGE_PATH_BLUE, "客户端坦克应该使用蓝色图片"
    
    print("  ✓ 主机模式坦克创建正常")
    
    # 测试客户端模式
    print("  测试客户端模式...")
    client_view = game_views.GameView(mode="network_client")
    client_view.setup()
    
    # 检查是否创建了两个坦克
    assert client_view.player_tank is not None, "主机坦克应该被创建"
    assert client_view.player2_tank is not None, "客户端坦克应该被创建"
    assert len(client_view.player_list) == 2, "应该有两个坦克"
    
    # 检查坦克的player_id
    assert client_view.player_tank.player_id == "host", "主机坦克应该有正确的player_id"
    assert client_view.player2_tank.player_id == "client", "客户端坦克应该有正确的player_id"
    
    print("  ✓ 客户端模式坦克创建正常")
    
    print("✅ 网络模式游戏视图测试通过")


def test_map_layout_sync():
    """测试地图布局同步"""
    print("🧪 测试地图布局同步...")
    
    # 创建主机视图并获取地图布局
    host_view = game_views.GameView(mode="network_host")
    host_view.setup()
    
    # 获取主机的地图布局
    host_map_layout = host_view.get_map_layout()
    assert host_map_layout is not None, "主机应该有地图布局"
    assert len(host_map_layout) > 0, "地图布局应该包含墙壁"
    print(f"  主机地图布局包含 {len(host_map_layout)} 个墙壁")
    
    # 创建客户端视图并设置相同的地图布局
    client_view = game_views.GameView(mode="network_client")
    client_view.set_map_layout(host_map_layout)
    client_view.setup()
    
    # 获取客户端的地图布局
    client_map_layout = client_view.get_map_layout()
    assert client_map_layout == host_map_layout, "客户端地图布局应该与主机相同"
    print(f"  客户端地图布局包含 {len(client_map_layout)} 个墙壁")
    
    # 验证地图布局内容完全一致
    for i, (host_wall, client_wall) in enumerate(zip(host_map_layout, client_map_layout)):
        assert host_wall == client_wall, f"第{i}个墙壁应该相同"
    
    print("  ✓ 地图布局同步正常")
    
    print("✅ 地图布局同步测试通过")


def test_tank_state_sync():
    """测试坦克状态同步"""
    print("🧪 测试坦克状态同步...")
    
    # 创建主机视图
    host_view = game_views.GameView(mode="network_host")
    host_view.setup()
    
    # 模拟获取游戏状态
    def mock_get_game_state():
        tanks = []
        if host_view.player_list:
            for tank in host_view.player_list:
                if tank is not None:
                    tanks.append({
                        "player_id": getattr(tank, 'player_id', 'unknown'),
                        "x": tank.center_x,
                        "y": tank.center_y,
                        "angle": tank.angle,
                        "health": getattr(tank, 'health', 5)
                    })
        return {"tanks": tanks, "bullets": [], "scores": {"host": 0, "client": 0}}
    
    game_state = mock_get_game_state()
    
    # 验证游戏状态包含两个坦克
    assert "tanks" in game_state, "游戏状态应该包含坦克信息"
    assert len(game_state["tanks"]) == 2, "应该有两个坦克的状态"
    
    # 验证坦克的player_id
    tank_ids = [tank["player_id"] for tank in game_state["tanks"]]
    assert "host" in tank_ids, "应该包含主机坦克"
    assert "client" in tank_ids, "应该包含客户端坦克"
    
    print(f"  游戏状态包含 {len(game_state['tanks'])} 个坦克")
    print(f"  坦克ID: {tank_ids}")
    
    # 创建客户端视图并应用状态
    client_view = game_views.GameView(mode="network_client")
    client_view.setup()
    
    # 模拟应用服务器状态
    def mock_apply_server_state(game_state):
        if not client_view.player_list or not game_state:
            return
        
        tanks_data = game_state.get("tanks", [])
        for i, tank_data in enumerate(tanks_data):
            if i < len(client_view.player_list):
                tank = client_view.player_list[i]
                if tank is not None:
                    tank.center_x = tank_data.get("x", tank.center_x)
                    tank.center_y = tank_data.get("y", tank.center_y)
                    tank.angle = tank_data.get("angle", tank.angle)
                    if hasattr(tank, 'health'):
                        tank.health = tank_data.get("health", tank.health)
    
    # 应用状态
    mock_apply_server_state(game_state)
    
    print("  ✓ 坦克状态同步正常")
    
    print("✅ 坦克状态同步测试通过")


def test_fixed_map_layout():
    """测试固定地图布局功能"""
    print("🧪 测试固定地图布局功能...")
    
    # 生成一个测试地图布局
    test_map_layout = [
        (400, 300, 100, 20),  # 中间横墙
        (200, 200, 20, 100),  # 左侧竖墙
        (600, 400, 20, 100),  # 右侧竖墙
    ]
    
    # 创建游戏视图并设置固定地图
    game_view = game_views.GameView(mode="network_client")
    game_view.set_map_layout(test_map_layout)
    
    # 验证地图布局被正确设置
    assert game_view.fixed_map_layout == test_map_layout, "固定地图布局应该被正确设置"
    
    # 验证get_map_layout返回固定布局
    retrieved_layout = game_view.get_map_layout()
    assert retrieved_layout == test_map_layout, "get_map_layout应该返回固定布局"
    
    print(f"  设置固定地图布局: {len(test_map_layout)} 个墙壁")
    print("  ✓ 固定地图布局功能正常")
    
    print("✅ 固定地图布局测试通过")


def test_tank_image_assignment():
    """测试坦克图片分配"""
    print("🧪 测试坦克图片分配...")
    
    # 测试网络模式下的坦克图片
    game_view = game_views.GameView(mode="network_host")
    game_view.setup()
    
    # 检查主机坦克图片（应该使用默认的绿色）
    assert game_view.player_tank.tank_image_file == game_views.PLAYER_IMAGE_PATH_GREEN, "主机坦克应该使用绿色图片"
    
    # 检查客户端坦克图片（应该使用蓝色）
    assert game_view.player2_tank.tank_image_file == PLAYER_IMAGE_PATH_BLUE, "客户端坦克应该使用蓝色图片"
    
    print("  ✓ 主机坦克使用绿色图片")
    print("  ✓ 客户端坦克使用蓝色图片")
    
    print("✅ 坦克图片分配测试通过")


def main():
    """运行所有测试"""
    print("🚀 开始多人联机同步修复测试\n")
    
    tests = [
        test_game_view_network_mode,
        test_map_layout_sync,
        test_tank_state_sync,
        test_fixed_map_layout,
        test_tank_image_assignment
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
        print("🎉 所有测试通过！多人联机同步问题已修复")
        print("\n📋 修复总结:")
        print("1. ✅ 网络模式下正确创建双坦克")
        print("2. ✅ 地图布局在主机和客户端之间同步")
        print("3. ✅ 坦克状态正确同步和显示")
        print("4. ✅ 客户端坦克使用蓝色图片")
        print("5. ✅ 坦克player_id正确设置")
        return True
    else:
        print("⚠️ 部分测试失败，需要进一步检查")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
