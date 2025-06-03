#!/usr/bin/env python3
"""
客户端视图切换循环问题修复测试

测试修复的具体问题：
1. 视图切换死循环 - 防止重复执行视图切换
2. 重复的调度任务 - 确保调度任务只执行一次
3. 线程安全问题 - 网络线程和主线程之间的视图切换保护

运行方法：
python test_client_view_switch_fix.py
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # 模拟arcade模块，避免在测试环境中的依赖问题
    mock_arcade = Mock()
    mock_arcade.color = Mock()
    mock_arcade.key = Mock()
    mock_arcade.View = Mock
    mock_arcade.Text = Mock
    mock_arcade.set_background_color = Mock()
    mock_arcade.schedule = Mock()
    mock_arcade.unschedule = Mock()
    
    sys.modules['arcade'] = mock_arcade
    sys.modules['arcade.color'] = mock_arcade.color
    sys.modules['arcade.key'] = mock_arcade.key
    
    # 导入要测试的模块
    from multiplayer.network_views import ClientGameView
    
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保在tank目录下运行此测试")
    sys.exit(1)


class TestClientViewSwitchFix(unittest.TestCase):
    """客户端视图切换修复测试类"""
    
    def setUp(self):
        """测试前的设置"""
        # 重置mock
        mock_arcade.schedule.reset_mock()
        mock_arcade.unschedule.reset_mock()
        
        # 创建客户端视图实例
        self.client_view = ClientGameView()
        self.client_view.window = Mock()
        self.client_view.window.invalid = False

    def test_view_switch_protection_flags(self):
        """测试视图切换保护标志初始化"""
        print("  测试视图切换保护标志...")
        
        # 检查保护标志是否正确初始化
        self.assertFalse(self.client_view.is_switching_view, "is_switching_view应该初始化为False")
        self.assertIsNone(self.client_view.scheduled_switch_task, "scheduled_switch_task应该初始化为None")
        self.assertFalse(self.client_view.should_return_to_browser, "should_return_to_browser应该初始化为False")
        
        print("    ✅ 视图切换保护标志初始化正确")

    def test_prevent_duplicate_disconnect_handling(self):
        """测试防止重复处理断开连接"""
        print("  测试防止重复处理断开连接...")
        
        # 第一次调用_on_disconnected
        self.client_view._on_disconnected("测试断开")
        
        # 验证状态已设置
        self.assertTrue(self.client_view.is_switching_view, "第一次断开后应该设置切换标志")
        
        # 第二次调用_on_disconnected（模拟重复调用）
        with patch('builtins.print') as mock_print:
            self.client_view._on_disconnected("重复断开")
            
            # 验证重复调用被忽略
            mock_print.assert_any_call("视图切换已在进行中，忽略重复请求")
        
        print("    ✅ 重复断开连接处理被正确忽略")

    def test_schedule_task_management(self):
        """测试调度任务管理"""
        print("  测试调度任务管理...")
        
        # 模拟第一次断开连接
        self.client_view._on_disconnected("第一次断开")
        
        # 验证调度任务被创建
        self.assertIsNotNone(self.client_view.scheduled_switch_task, "应该创建调度任务")
        mock_arcade.schedule.assert_called_once()
        
        # 重置mock
        mock_arcade.schedule.reset_mock()
        mock_arcade.unschedule.reset_mock()
        
        # 重置切换标志，模拟第二次断开连接
        self.client_view.is_switching_view = False
        self.client_view._on_disconnected("第二次断开")
        
        # 验证之前的任务被取消，新任务被创建
        mock_arcade.unschedule.assert_called_once()
        mock_arcade.schedule.assert_called_once()
        
        print("    ✅ 调度任务管理正确")

    def test_on_update_protection(self):
        """测试on_update方法的保护机制"""
        print("  测试on_update保护机制...")
        
        # 设置回退标志
        self.client_view.should_return_to_browser = True
        self.client_view.is_switching_view = False
        
        # 调用on_update
        with patch('game_views.ModeSelectView') as mock_mode_view:
            self.client_view.on_update(0.016)
            
            # 验证视图切换被执行
            mock_mode_view.assert_called_once()
            self.assertFalse(self.client_view.should_return_to_browser, "回退标志应该被清除")
        
        # 测试保护机制 - 当is_switching_view为True时
        self.client_view.should_return_to_browser = True
        self.client_view.is_switching_view = True
        
        with patch('game_views.ModeSelectView') as mock_mode_view:
            self.client_view.on_update(0.016)
            
            # 验证视图切换被阻止
            mock_mode_view.assert_not_called()
            self.assertTrue(self.client_view.should_return_to_browser, "回退标志应该保持")
        
        print("    ✅ on_update保护机制正确")

    def test_esc_key_protection(self):
        """测试ESC键的保护机制"""
        print("  测试ESC键保护机制...")
        
        # 模拟ESC键按下
        with patch('game_views.ModeSelectView') as mock_mode_view:
            self.client_view.on_key_press(mock_arcade.key.ESCAPE, None)
            
            # 验证视图切换被执行
            mock_mode_view.assert_called_once()
        
        # 测试保护机制 - 当is_switching_view为True时
        self.client_view.is_switching_view = True
        
        with patch('game_views.ModeSelectView') as mock_mode_view:
            self.client_view.on_key_press(mock_arcade.key.ESCAPE, None)
            
            # 验证视图切换被阻止
            mock_mode_view.assert_not_called()
        
        print("    ✅ ESC键保护机制正确")

    def test_cleanup_on_hide_view(self):
        """测试视图隐藏时的清理"""
        print("  测试视图隐藏时的清理...")
        
        # 设置一些状态
        self.client_view.is_switching_view = True
        self.client_view.should_return_to_browser = True
        self.client_view.scheduled_switch_task = Mock()
        
        # 调用on_hide_view
        self.client_view.on_hide_view()
        
        # 验证状态被清理
        self.assertFalse(self.client_view.is_switching_view, "切换标志应该被重置")
        self.assertFalse(self.client_view.should_return_to_browser, "回退标志应该被重置")
        self.assertIsNone(self.client_view.scheduled_switch_task, "调度任务应该被清除")
        
        # 验证unschedule被调用
        mock_arcade.unschedule.assert_called_once()
        
        print("    ✅ 视图隐藏时的清理正确")

    def test_switch_view_function_error_handling(self):
        """测试switch_view函数的错误处理"""
        print("  测试switch_view函数错误处理...")
        
        # 模拟window.invalid为True的情况
        self.client_view.window.invalid = True
        
        # 调用_on_disconnected
        self.client_view._on_disconnected("测试断开")
        
        # 获取调度的函数
        self.assertTrue(mock_arcade.schedule.called, "应该调用了schedule")
        scheduled_func = mock_arcade.schedule.call_args[0][0]
        
        # 执行调度的函数
        with patch('builtins.print') as mock_print:
            scheduled_func(0.1)  # 传入delta_time参数
            
            # 验证错误处理
            self.assertFalse(self.client_view.is_switching_view, "切换标志应该被重置")
        
        print("    ✅ switch_view函数错误处理正确")


def run_tests():
    """运行所有测试"""
    print("🧪 开始客户端视图切换循环问题修复测试")
    print("=" * 60)
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestClientViewSwitchFix)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=0)
    result = runner.run(suite)
    
    print("=" * 60)
    if result.wasSuccessful():
        print("🎉 所有测试通过！客户端视图切换循环问题修复验证成功")
        print("\n修复内容总结：")
        print("✅ 1. 视图切换死循环 - 添加保护标志防止重复执行")
        print("✅ 2. 重复的调度任务 - 正确管理和清理调度任务")
        print("✅ 3. 线程安全问题 - 在所有视图切换点添加保护机制")
        print("✅ 4. 状态清理 - 视图隐藏时正确清理所有状态")
        print("✅ 5. 错误处理 - 完善的异常处理和状态恢复")
        return True
    else:
        print("❌ 部分测试失败，请检查修复代码")
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
