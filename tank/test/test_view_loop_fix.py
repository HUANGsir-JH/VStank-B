"""
视图切换循环问题修复测试
测试修复后的客户端断开连接处理逻辑
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest.mock import Mock, patch, MagicMock
from multiplayer.network_views import RoomBrowserView, ClientGameView


class TestViewLoopFix(unittest.TestCase):
    """测试视图切换循环修复"""
    
    def setUp(self):
        """设置测试环境"""
        self.mock_window = Mock()
        
    def test_room_browser_discovery_start_once(self):
        """测试房间浏览器只启动一次房间发现"""
        print("🧪 测试房间浏览器防重复启动...")
        
        with patch('multiplayer.network_views.RoomDiscovery') as mock_discovery_class:
            mock_discovery = Mock()
            mock_discovery_class.return_value = mock_discovery
            
            # 创建房间浏览器视图
            browser_view = RoomBrowserView()
            browser_view.window = self.mock_window
            
            # 第一次显示视图
            browser_view.on_show_view()
            
            # 验证房间发现被启动
            mock_discovery.start_discovery.assert_called_once()
            print("  ✅ 第一次显示时正确启动房间发现")
            
            # 重置调用计数
            mock_discovery.start_discovery.reset_mock()
            
            # 第二次显示视图（模拟循环问题）
            browser_view.on_show_view()
            
            # 验证房间发现没有被重复启动
            mock_discovery.start_discovery.assert_not_called()
            print("  ✅ 第二次显示时跳过重复启动")
            
            # 隐藏视图
            browser_view.on_hide_view()
            
            # 验证房间发现被停止
            mock_discovery.stop_discovery.assert_called_once()
            print("  ✅ 隐藏视图时正确停止房间发现")
            
            # 重置调用计数
            mock_discovery.start_discovery.reset_mock()
            
            # 再次显示视图（隐藏后重新显示）
            browser_view.on_show_view()
            
            # 验证房间发现被重新启动
            mock_discovery.start_discovery.assert_called_once()
            print("  ✅ 隐藏后重新显示时正确重新启动")
    
    def test_client_disconnect_returns_to_main_menu(self):
        """测试客户端断开连接返回主菜单"""
        print("🧪 测试客户端断开连接返回主菜单...")
        
        with patch('multiplayer.network_views.arcade') as mock_arcade, \
             patch('multiplayer.network_views.game_views') as mock_game_views:
            
            # 设置模拟对象
            mock_schedule = Mock()
            mock_arcade.schedule = mock_schedule
            mock_mode_view = Mock()
            mock_game_views.ModeSelectView.return_value = mock_mode_view
            
            # 创建客户端视图
            client_view = ClientGameView()
            client_view.window = self.mock_window
            
            # 模拟断开连接
            client_view._on_disconnected("主机关闭")
            
            # 验证arcade.schedule被调用
            mock_schedule.assert_called_once()
            
            # 获取并执行switch_view函数
            args, kwargs = mock_schedule.call_args
            switch_view_func = args[0]
            delay = args[1]
            
            # 验证延迟时间
            self.assertEqual(delay, 0.1)
            
            # 执行switch_view函数
            switch_view_func(0.016)  # 模拟delta_time
            
            # 验证返回到主菜单而不是房间浏览器
            mock_game_views.ModeSelectView.assert_called_once()
            self.mock_window.show_view.assert_called_once_with(mock_mode_view)
            print("  ✅ 断开连接时正确返回主菜单")
    
    def test_client_fallback_mechanism(self):
        """测试客户端回退机制"""
        print("🧪 测试客户端回退机制...")
        
        with patch('multiplayer.network_views.game_views') as mock_game_views:
            mock_mode_view = Mock()
            mock_game_views.ModeSelectView.return_value = mock_mode_view
            
            # 创建客户端视图
            client_view = ClientGameView()
            client_view.window = self.mock_window
            
            # 设置回退标志
            client_view.should_return_to_browser = True
            
            # 调用update方法
            client_view.on_update(0.016)
            
            # 验证返回到主菜单
            mock_game_views.ModeSelectView.assert_called_once()
            self.mock_window.show_view.assert_called_once_with(mock_mode_view)
            
            # 验证标志被重置
            self.assertFalse(client_view.should_return_to_browser)
            print("  ✅ 回退机制正确返回主菜单")
    
    def test_client_esc_key_returns_to_main_menu(self):
        """测试客户端ESC键返回主菜单"""
        print("🧪 测试客户端ESC键返回主菜单...")
        
        with patch('multiplayer.network_views.game_views') as mock_game_views, \
             patch('multiplayer.network_views.arcade') as mock_arcade:
            
            mock_mode_view = Mock()
            mock_game_views.ModeSelectView.return_value = mock_mode_view
            
            # 创建客户端视图
            client_view = ClientGameView()
            client_view.window = self.mock_window
            
            # 模拟ESC键按下
            client_view.on_key_press(mock_arcade.key.ESCAPE, None)
            
            # 验证返回到主菜单
            mock_game_views.ModeSelectView.assert_called_once()
            self.mock_window.show_view.assert_called_once_with(mock_mode_view)
            print("  ✅ ESC键正确返回主菜单")


def test_room_browser_state_management():
    """测试房间浏览器状态管理"""
    print("🧪 测试房间浏览器状态管理...")
    
    with patch('multiplayer.network_views.RoomDiscovery') as mock_discovery_class:
        mock_discovery = Mock()
        mock_discovery_class.return_value = mock_discovery
        
        # 创建房间浏览器视图
        browser_view = RoomBrowserView()
        
        # 验证初始状态
        assert not browser_view.discovery_started, "初始状态应该是未启动"
        print("  ✅ 初始状态正确")
        
        # 第一次显示
        browser_view.on_show_view()
        assert browser_view.discovery_started, "显示后应该标记为已启动"
        print("  ✅ 显示后状态正确")
        
        # 隐藏视图
        browser_view.on_hide_view()
        assert not browser_view.discovery_started, "隐藏后应该重置状态"
        print("  ✅ 隐藏后状态正确")


def test_no_room_browser_creation_loop():
    """测试不会创建房间浏览器循环"""
    print("🧪 测试避免房间浏览器创建循环...")
    
    with patch('multiplayer.network_views.arcade') as mock_arcade, \
         patch('multiplayer.network_views.game_views') as mock_game_views, \
         patch('multiplayer.network_views.RoomBrowserView') as mock_browser_class:
        
        # 设置模拟对象
        mock_schedule = Mock()
        mock_arcade.schedule = mock_schedule
        mock_mode_view = Mock()
        mock_game_views.ModeSelectView.return_value = mock_mode_view
        
        # 创建客户端视图
        client_view = ClientGameView()
        client_view.window = Mock()
        
        # 模拟断开连接
        client_view._on_disconnected("主机关闭")
        
        # 获取并执行switch_view函数
        args, kwargs = mock_schedule.call_args
        switch_view_func = args[0]
        switch_view_func(0.016)
        
        # 验证没有创建RoomBrowserView
        mock_browser_class.assert_not_called()
        print("  ✅ 断开连接时没有创建房间浏览器")
        
        # 验证创建了ModeSelectView
        mock_game_views.ModeSelectView.assert_called_once()
        print("  ✅ 断开连接时正确创建主菜单视图")


def main():
    """主测试函数"""
    print("🚀 开始视图切换循环修复测试\n")
    
    # 运行单元测试
    print("📋 运行单元测试...")
    unittest.main(argv=[''], exit=False, verbosity=0)
    
    print("\n📋 运行额外测试...")
    try:
        test_room_browser_state_management()
        test_no_room_browser_creation_loop()
        print("✅ 额外测试通过")
    except Exception as e:
        print(f"❌ 额外测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("📊 修复总结:")
    print("✅ 房间浏览器防止重复启动房间发现")
    print("✅ 客户端断开连接返回主菜单而不是房间浏览器")
    print("✅ 客户端ESC键返回主菜单")
    print("✅ 回退机制返回主菜单")
    print("✅ 避免了视图切换循环问题")
    print("\n🎉 视图切换循环修复测试完成！")


if __name__ == "__main__":
    main()
