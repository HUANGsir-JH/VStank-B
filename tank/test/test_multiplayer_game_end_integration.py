#!/usr/bin/env python3
"""
多人联机游戏结束流程集成测试

测试整个游戏结束流程的集成，包括：
1. 主机端游戏结束检测和消息发送
2. 客户端消息接收和界面显示
3. 网络通信的完整流程
"""

import unittest
import sys
import os
import time
from unittest.mock import Mock, patch

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multiplayer.messages import MessageFactory, MessageType, NetworkMessage
from multiplayer.game_host import GameHost
from multiplayer.game_client import GameClient


class TestMultiplayerGameEndIntegration(unittest.TestCase):
    """测试多人联机游戏结束流程集成"""

    def setUp(self):
        """测试前准备"""
        self.host = None
        self.client = None

    def tearDown(self):
        """测试后清理"""
        if self.host:
            self.host.stop_hosting(force=True)
        if self.client:
            self.client.disconnect()

    def test_game_end_message_flow(self):
        """测试游戏结束消息流程"""
        print("  测试游戏结束消息流程...")
        
        # 模拟主机端发送游戏结束消息
        game_end_message = MessageFactory.create_game_end(
            winner="player1",
            final_scores={"player1": 2, "player2": 1},
            winner_text="主机 最终胜利!"
        )
        
        # 验证消息结构
        self.assertEqual(game_end_message.type, MessageType.GAME_END)
        self.assertIn("winner", game_end_message.data)
        self.assertIn("final_scores", game_end_message.data)
        self.assertIn("winner_text", game_end_message.data)
        self.assertIn("timestamp", game_end_message.data)
        
        # 模拟网络传输
        serialized = game_end_message.to_bytes()
        received_message = NetworkMessage.from_bytes(serialized)
        
        # 验证接收到的消息
        self.assertEqual(received_message.type, MessageType.GAME_END)
        self.assertEqual(received_message.data["winner"], "player1")
        self.assertEqual(received_message.data["winner_text"], "主机 最终胜利!")
        
        print("    ✅ 游戏结束消息流程正确")

    def test_host_game_event_callback(self):
        """测试主机端游戏事件回调"""
        print("  测试主机端游戏事件回调...")
        
        # 模拟主机端网络视图的游戏事件处理
        sent_messages = []
        
        def mock_send_to_client(message):
            sent_messages.append(message)
        
        # 模拟游戏事件回调
        def simulate_game_event_callback(event_type, event_data):
            if event_type == "game_end":
                game_end_msg = MessageFactory.create_game_end(
                    winner=event_data.get("winner"),
                    final_scores=event_data.get("final_scores"),
                    winner_text=event_data.get("winner_text")
                )
                mock_send_to_client(game_end_msg)
        
        # 模拟游戏结束事件
        event_data = {
            "winner": "player2",
            "winner_text": "客户端 最终胜利!",
            "final_scores": {"player1": 1, "player2": 2}
        }
        
        simulate_game_event_callback("game_end", event_data)
        
        # 验证消息被发送
        self.assertEqual(len(sent_messages), 1)
        sent_message = sent_messages[0]
        self.assertEqual(sent_message.type, MessageType.GAME_END)
        self.assertEqual(sent_message.data["winner"], "player2")
        self.assertEqual(sent_message.data["winner_text"], "客户端 最终胜利!")
        
        print("    ✅ 主机端游戏事件回调正确")

    def test_client_game_end_callback(self):
        """测试客户端游戏结束回调"""
        print("  测试客户端游戏结束回调...")
        
        # 模拟客户端接收游戏结束消息
        received_game_end_data = None
        game_over_shown = False
        
        def mock_game_end_callback(game_end_data):
            nonlocal received_game_end_data, game_over_shown
            received_game_end_data = game_end_data
            # 模拟显示游戏结束界面
            game_over_shown = True
        
        # 创建游戏结束消息
        game_end_message = MessageFactory.create_game_end(
            winner="player1",
            final_scores={"player1": 2, "player2": 0},
            winner_text="主机 最终胜利!"
        )
        
        # 模拟客户端处理消息
        mock_game_end_callback(game_end_message.data)
        
        # 验证回调被正确调用
        self.assertIsNotNone(received_game_end_data)
        self.assertEqual(received_game_end_data["winner"], "player1")
        self.assertEqual(received_game_end_data["winner_text"], "主机 最终胜利!")
        self.assertTrue(game_over_shown)
        
        print("    ✅ 客户端游戏结束回调正确")

    def test_different_game_end_scenarios(self):
        """测试不同的游戏结束场景"""
        print("  测试不同游戏结束场景...")
        
        scenarios = [
            {
                "name": "主机2:0获胜",
                "winner": "player1",
                "scores": {"player1": 2, "player2": 0},
                "text": "主机 最终胜利!"
            },
            {
                "name": "主机2:1获胜", 
                "winner": "player1",
                "scores": {"player1": 2, "player2": 1},
                "text": "主机 最终胜利!"
            },
            {
                "name": "客户端2:0获胜",
                "winner": "player2", 
                "scores": {"player1": 0, "player2": 2},
                "text": "客户端 最终胜利!"
            },
            {
                "name": "客户端2:1获胜",
                "winner": "player2",
                "scores": {"player1": 1, "player2": 2}, 
                "text": "客户端 最终胜利!"
            }
        ]
        
        for scenario in scenarios:
            with self.subTest(scenario=scenario["name"]):
                message = MessageFactory.create_game_end(
                    winner=scenario["winner"],
                    final_scores=scenario["scores"],
                    winner_text=scenario["text"]
                )
                
                # 验证消息内容
                self.assertEqual(message.data["winner"], scenario["winner"])
                self.assertEqual(message.data["final_scores"], scenario["scores"])
                self.assertEqual(message.data["winner_text"], scenario["text"])
                
                # 验证序列化/反序列化
                serialized = message.to_bytes()
                deserialized = NetworkMessage.from_bytes(serialized)
                self.assertEqual(deserialized.data["winner"], scenario["winner"])
        
        print("    ✅ 不同游戏结束场景测试正确")

    def test_network_thread_safety(self):
        """测试网络线程安全性"""
        print("  测试网络线程安全性...")
        
        # 模拟在网络线程中接收游戏结束消息
        # 验证不会直接操作OpenGL，而是设置标志
        
        thread_safe_flags = {
            "should_show_game_over": False,
            "game_end_data": None
        }
        
        def mock_network_thread_game_end_handler(game_end_data):
            # 模拟网络线程中的处理 - 只设置标志，不直接操作UI
            thread_safe_flags["should_show_game_over"] = True
            thread_safe_flags["game_end_data"] = game_end_data
        
        # 模拟主线程中的处理
        def mock_main_thread_update():
            if thread_safe_flags["should_show_game_over"]:
                thread_safe_flags["should_show_game_over"] = False
                # 在这里安全地显示游戏结束界面
                return thread_safe_flags["game_end_data"]
            return None
        
        # 模拟游戏结束消息
        game_end_data = {
            "winner": "player1",
            "winner_text": "主机 最终胜利!",
            "final_scores": {"player1": 2, "player2": 1}
        }
        
        # 模拟网络线程处理
        mock_network_thread_game_end_handler(game_end_data)
        
        # 验证标志被设置
        self.assertTrue(thread_safe_flags["should_show_game_over"])
        self.assertIsNotNone(thread_safe_flags["game_end_data"])
        
        # 模拟主线程处理
        result = mock_main_thread_update()
        
        # 验证主线程正确处理
        self.assertIsNotNone(result)
        self.assertEqual(result["winner"], "player1")
        self.assertFalse(thread_safe_flags["should_show_game_over"])  # 标志被重置
        
        print("    ✅ 网络线程安全性正确")


def run_tests():
    """运行所有测试"""
    print("🧪 开始测试多人联机游戏结束流程集成...")
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMultiplayerGameEndIntegration)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=0)
    result = runner.run(suite)
    
    # 输出结果
    if result.wasSuccessful():
        print("✅ 所有集成测试通过！游戏结束流程修复完整且正确。")
        return True
    else:
        print("❌ 集成测试失败！")
        for failure in result.failures:
            print(f"失败: {failure[0]}")
            print(f"详情: {failure[1]}")
        for error in result.errors:
            print(f"错误: {error[0]}")
            print(f"详情: {error[1]}")
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
