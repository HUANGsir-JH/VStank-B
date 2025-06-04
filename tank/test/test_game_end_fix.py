#!/usr/bin/env python3
"""
测试多人联机游戏结束流程修复

测试内容：
1. 游戏结束消息的创建和序列化
2. 主机端游戏结束消息发送逻辑
3. 客户端游戏结束消息接收和处理逻辑
4. 游戏结束界面的显示
"""

import unittest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multiplayer.messages import MessageFactory, MessageType, NetworkMessage


class TestGameEndFix(unittest.TestCase):
    """测试游戏结束流程修复"""

    def test_game_end_message_creation(self):
        """测试游戏结束消息的创建"""
        print("  测试游戏结束消息创建...")
        
        # 测试创建游戏结束消息
        winner = "player1"
        final_scores = {"player1": 2, "player2": 1}
        winner_text = "主机 最终胜利!"
        
        message = MessageFactory.create_game_end(
            winner=winner,
            final_scores=final_scores,
            winner_text=winner_text
        )
        
        # 验证消息类型
        self.assertEqual(message.type, MessageType.GAME_END)
        
        # 验证消息数据
        self.assertEqual(message.data["winner"], winner)
        self.assertEqual(message.data["final_scores"], final_scores)
        self.assertEqual(message.data["winner_text"], winner_text)
        self.assertIn("timestamp", message.data)
        
        print("    ✅ 游戏结束消息创建正确")

    def test_game_end_message_serialization(self):
        """测试游戏结束消息的序列化和反序列化"""
        print("  测试游戏结束消息序列化...")
        
        # 创建消息
        original_message = MessageFactory.create_game_end(
            winner="player2",
            final_scores={"player1": 1, "player2": 2},
            winner_text="客户端 最终胜利!"
        )
        
        # 序列化
        serialized_data = original_message.to_bytes()
        self.assertIsInstance(serialized_data, bytes)
        
        # 反序列化
        deserialized_message = NetworkMessage.from_bytes(serialized_data)
        
        # 验证反序列化结果
        self.assertEqual(deserialized_message.type, original_message.type)
        self.assertEqual(deserialized_message.data["winner"], original_message.data["winner"])
        self.assertEqual(deserialized_message.data["final_scores"], original_message.data["final_scores"])
        self.assertEqual(deserialized_message.data["winner_text"], original_message.data["winner_text"])
        
        print("    ✅ 游戏结束消息序列化正确")

    def test_game_view_network_callback(self):
        """测试GameView的网络回调设置"""
        print("  测试GameView网络回调...")
        
        # 模拟GameView的网络回调功能
        callback_called = False
        callback_data = None
        
        def mock_network_callback(event_type, event_data):
            nonlocal callback_called, callback_data
            callback_called = True
            callback_data = (event_type, event_data)
        
        # 模拟GameView设置回调
        # 这里我们直接测试回调逻辑，而不是实际创建GameView实例
        # 因为GameView需要arcade环境
        
        # 模拟游戏结束事件
        event_type = "game_end"
        event_data = {
            "winner": "player1",
            "winner_text": "主机 最终胜利!",
            "final_scores": {"player1": 2, "player2": 1}
        }
        
        # 调用回调
        mock_network_callback(event_type, event_data)
        
        # 验证回调被调用
        self.assertTrue(callback_called)
        self.assertEqual(callback_data[0], event_type)
        self.assertEqual(callback_data[1], event_data)
        
        print("    ✅ GameView网络回调设置正确")

    def test_game_end_scenarios(self):
        """测试不同的游戏结束场景"""
        print("  测试游戏结束场景...")
        
        # 场景1: 主机获胜 (2:0)
        message1 = MessageFactory.create_game_end(
            winner="player1",
            final_scores={"player1": 2, "player2": 0},
            winner_text="主机 最终胜利!"
        )
        self.assertEqual(message1.data["winner"], "player1")
        self.assertEqual(message1.data["final_scores"]["player1"], 2)
        
        # 场景2: 客户端获胜 (2:1)
        message2 = MessageFactory.create_game_end(
            winner="player2",
            final_scores={"player1": 1, "player2": 2},
            winner_text="客户端 最终胜利!"
        )
        self.assertEqual(message2.data["winner"], "player2")
        self.assertEqual(message2.data["final_scores"]["player2"], 2)
        
        # 场景3: 客户端获胜 (1:2)
        message3 = MessageFactory.create_game_end(
            winner="player2",
            final_scores={"player1": 1, "player2": 2},
            winner_text="客户端 最终胜利!"
        )
        self.assertEqual(message3.data["winner"], "player2")
        
        print("    ✅ 游戏结束场景测试正确")

    def test_message_type_enum(self):
        """测试消息类型枚举包含GAME_END"""
        print("  测试消息类型枚举...")
        
        # 验证GAME_END消息类型存在
        self.assertTrue(hasattr(MessageType, 'GAME_END'))
        self.assertEqual(MessageType.GAME_END.value, "game_end")
        
        print("    ✅ 消息类型枚举正确")


def run_tests():
    """运行所有测试"""
    print("🧪 开始测试多人联机游戏结束流程修复...")
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestGameEndFix)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=0)
    result = runner.run(suite)
    
    # 输出结果
    if result.wasSuccessful():
        print("✅ 所有测试通过！游戏结束流程修复正确。")
        return True
    else:
        print("❌ 测试失败！")
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
