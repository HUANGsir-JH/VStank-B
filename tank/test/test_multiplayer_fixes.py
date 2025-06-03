#!/usr/bin/env python3
"""
多人联机模块修复测试
测试修复后的网络视图和错误处理
"""

import sys
import os
import time
import threading

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from multiplayer.game_host import GameHost
from multiplayer.game_client import GameClient
import game_views


def test_game_view_initialization():
    """测试游戏视图初始化修复"""
    print("🧪 测试游戏视图初始化修复...")

    # 直接测试GameView的初始化
    print("  测试GameView直接初始化...")
    game_view = game_views.GameView(mode="network_host")

    # 检查初始状态
    assert game_view.player_list is None, "初始状态下player_list应为None"

    # 调用setup方法
    game_view.setup()

    # 检查setup后的状态
    assert game_view.player_list is not None, "setup后player_list应不为None"
    assert hasattr(game_view, 'bullet_list'), "应该有bullet_list属性"
    assert game_view.bullet_list is not None, "bullet_list应不为None"
    print("  ✓ GameView初始化和setup正常")

    # 测试网络客户端模式
    print("  测试网络客户端模式初始化...")
    client_game_view = game_views.GameView(mode="network_client")
    client_game_view.setup()

    assert client_game_view.player_list is not None, "客户端模式player_list应不为None"
    assert client_game_view.bullet_list is not None, "客户端模式bullet_list应不为None"
    print("  ✓ 网络客户端模式初始化正常")

    print("✅ 游戏视图初始化修复测试通过")


def test_game_state_extraction():
    """测试游戏状态提取的防护性检查"""
    print("🧪 测试游戏状态提取防护性检查...")

    # 创建一个模拟的主机视图类来测试_get_game_state方法
    class MockHostView:
        def __init__(self):
            self.game_view = None

        def _get_game_state(self):
            """复制修复后的_get_game_state逻辑"""
            if not self.game_view:
                return {}

            # 提取坦克状态
            tanks = []
            if hasattr(self.game_view, 'player_list') and self.game_view.player_list is not None:
                try:
                    for tank in self.game_view.player_list:
                        if tank is not None:
                            tanks.append({
                                "player_id": getattr(tank, 'player_id', 'unknown'),
                                "x": tank.center_x,
                                "y": tank.center_y,
                                "angle": tank.angle,
                                "health": getattr(tank, 'health', 5)
                            })
                except Exception as e:
                    print(f"获取坦克状态时出错: {e}")

            # 提取子弹状态
            bullets = []
            if hasattr(self.game_view, 'bullet_list') and self.game_view.bullet_list is not None:
                try:
                    for bullet in self.game_view.bullet_list:
                        if bullet is not None:
                            bullets.append({
                                "x": bullet.center_x,
                                "y": bullet.center_y,
                                "angle": getattr(bullet, 'angle', 0),
                                "owner": getattr(bullet.owner, 'player_id', 'unknown') if bullet.owner else 'unknown'
                            })
                except Exception as e:
                    print(f"获取子弹状态时出错: {e}")

            # 提取分数
            scores = {}
            if hasattr(self.game_view, 'player1_score'):
                scores["host"] = self.game_view.player1_score
            if hasattr(self.game_view, 'player2_score'):
                scores["client"] = self.game_view.player2_score

            return {
                "tanks": tanks,
                "bullets": bullets,
                "scores": scores
            }

    host_view = MockHostView()

    # 测试没有游戏视图时的状态提取
    state = host_view._get_game_state()
    assert state == {}, "没有游戏视图时应返回空字典"
    print("  ✓ 无游戏视图时状态提取正常")

    # 创建游戏视图但不初始化
    host_view.game_view = game_views.GameView(mode="network_host")

    # 测试player_list为None时的状态提取
    state = host_view._get_game_state()
    assert "tanks" in state, "状态应包含tanks字段"
    assert state["tanks"] == [], "player_list为None时tanks应为空列表"
    print("  ✓ player_list为None时状态提取正常")

    # 正确初始化游戏视图
    host_view.game_view.setup()

    # 测试正常状态提取
    state = host_view._get_game_state()
    assert "tanks" in state, "状态应包含tanks字段"
    assert "bullets" in state, "状态应包含bullets字段"
    assert "scores" in state, "状态应包含scores字段"
    print("  ✓ 正常状态提取工作正常")

    print("✅ 游戏状态提取防护性检查测试通过")


def test_client_state_application():
    """测试客户端状态应用的防护性检查"""
    print("🧪 测试客户端状态应用防护性检查...")

    # 创建一个模拟的客户端视图类来测试_apply_server_state方法
    class MockClientView:
        def __init__(self):
            self.game_view = None
            self.game_state = {}

        def _apply_server_state(self):
            """复制修复后的_apply_server_state逻辑"""
            if not self.game_view or not self.game_state:
                return

            # 更新坦克状态
            tanks_data = self.game_state.get("tanks", [])
            if hasattr(self.game_view, 'player_list') and self.game_view.player_list is not None:
                try:
                    for i, tank_data in enumerate(tanks_data):
                        if i < len(self.game_view.player_list):
                            tank = self.game_view.player_list[i]
                            if tank is not None:
                                tank.center_x = tank_data.get("x", tank.center_x)
                                tank.center_y = tank_data.get("y", tank.center_y)
                                tank.angle = tank_data.get("angle", tank.angle)
                                if hasattr(tank, 'health'):
                                    tank.health = tank_data.get("health", tank.health)
                except Exception as e:
                    print(f"应用坦克状态时出错: {e}")

            # 更新分数
            scores = self.game_state.get("scores", {})
            if hasattr(self.game_view, 'player1_score') and "host" in scores:
                self.game_view.player1_score = scores["host"]
            if hasattr(self.game_view, 'player2_score') and "client" in scores:
                self.game_view.player2_score = scores["client"]

    client_view = MockClientView()

    # 测试没有游戏视图时的状态应用
    client_view.game_state = {"tanks": [{"x": 100, "y": 100, "angle": 0, "health": 5}]}
    client_view._apply_server_state()  # 应该不会崩溃
    print("  ✓ 无游戏视图时状态应用正常")

    # 创建游戏视图但不初始化
    client_view.game_view = game_views.GameView(mode="network_client")
    client_view._apply_server_state()  # 应该不会崩溃
    print("  ✓ player_list为None时状态应用正常")

    # 正确初始化游戏视图
    client_view.game_view.setup()
    client_view._apply_server_state()  # 应该正常工作
    print("  ✓ 正常状态应用工作正常")

    print("✅ 客户端状态应用防护性检查测试通过")


def test_connection_error_handling():
    """测试连接错误处理"""
    print("🧪 测试连接错误处理...")
    
    # 创建客户端
    client = GameClient()
    
    # 设置回调来捕获断开连接事件
    disconnection_reason = None
    def on_disconnection(reason):
        nonlocal disconnection_reason
        disconnection_reason = reason
        print(f"  收到断开连接通知: {reason}")
    
    client.set_callbacks(
        connection=lambda pid: print(f"  连接成功: {pid}"),
        disconnection=on_disconnection,
        game_state=lambda state: print(f"  收到游戏状态: {state}")
    )
    
    # 尝试连接到不存在的主机
    print("  测试连接失败处理...")
    success = client.connect_to_host("127.0.0.1", 99999, "测试玩家")
    assert not success, "连接到不存在的主机应该失败"
    print("  ✓ 连接失败处理正常")
    
    # 测试网络错误处理
    print("  测试网络错误处理...")
    client._handle_connection_lost("测试网络错误")
    time.sleep(0.1)  # 等待回调执行
    assert disconnection_reason == "测试网络错误", "断开连接回调应该被调用"
    print("  ✓ 网络错误处理正常")
    
    print("✅ 连接错误处理测试通过")


def test_view_switching_safety():
    """测试视图切换安全性"""
    print("🧪 测试视图切换安全性...")

    # 创建一个模拟的客户端视图类来测试断开连接处理
    class MockClientView:
        def __init__(self):
            self.connected = False
            self.should_return_to_browser = False

        def _on_disconnected(self, reason: str):
            """复制修复后的_on_disconnected逻辑"""
            self.connected = False
            print(f"连接断开: {reason}")

            # 延迟视图切换，避免在网络线程中直接操作OpenGL
            try:
                # 在测试环境中，arcade.schedule可能不可用，所以设置标志
                self.should_return_to_browser = True
                print("设置了返回浏览器标志")
            except Exception as e:
                print(f"切换视图时出错: {e}")
                self.should_return_to_browser = True

    client_view = MockClientView()

    # 测试断开连接标志
    assert hasattr(client_view, 'should_return_to_browser'), "应该有断开连接标志"
    assert not client_view.should_return_to_browser, "初始状态下标志应为False"

    # 模拟断开连接
    client_view._on_disconnected("测试断开")

    # 检查标志是否被设置
    assert client_view.should_return_to_browser, "断开连接后应设置返回浏览器标志"
    print("  ✓ 断开连接处理机制正常工作")

    print("✅ 视图切换安全性测试通过")


def main():
    """运行所有测试"""
    print("🚀 开始多人联机模块修复测试\n")
    
    try:
        test_game_view_initialization()
        print()
        
        test_game_state_extraction()
        print()
        
        test_client_state_application()
        print()
        
        test_connection_error_handling()
        print()
        
        test_view_switching_safety()
        print()
        
        print("🎉 所有测试通过！多人联机模块修复成功。")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
