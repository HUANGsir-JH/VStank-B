#!/usr/bin/env python3
"""
FPS同步集成测试

测试修复后的多人联机系统中主机端和客户端的刷新率同步效果。
"""

import sys
import os
import time
import threading
from unittest.mock import Mock, patch

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from fps_config import FPSConfig, NetworkSyncOptimizer, get_fps_config, set_fps_config
    from multiplayer.game_host import GameHost
    from multiplayer.game_client import GameClient
except ImportError as e:
    print(f"❌ 导入模块失败: {e}")
    print("请确保在tank目录下运行此测试")
    sys.exit(1)


class FPSSyncIntegrationTest:
    """FPS同步集成测试类"""
    
    def __init__(self):
        self.test_results = {}
        
    def test_unified_fps_config(self):
        """测试统一FPS配置"""
        print("🎯 测试统一FPS配置...")
        
        try:
            # 测试默认配置
            fps_config = get_fps_config()
            assert fps_config.target_fps == 60, f"默认目标FPS错误: {fps_config.target_fps}"
            assert fps_config.network_sync_fps == 60, f"默认网络同步FPS错误: {fps_config.network_sync_fps}"
            
            # 测试配置切换
            balanced_config = set_fps_config("balanced")
            assert balanced_config.target_fps == 60, "平衡模式目标FPS错误"
            assert balanced_config.network_sync_fps == 45, "平衡模式网络同步FPS错误"
            
            # 测试性能模式
            high_perf_config = set_fps_config("high_performance")
            assert high_perf_config.target_fps == 60, "高性能模式目标FPS错误"
            assert high_perf_config.network_sync_fps == 60, "高性能模式网络同步FPS错误"
            
            # 测试物理更新限制
            physics_limit = high_perf_config.get_physics_delta_limit()
            expected_limit = 1.0 / 60.0
            assert abs(physics_limit - expected_limit) < 0.001, f"物理更新限制错误: {physics_limit}"
            
            print("✅ 统一FPS配置测试通过")
            return True
            
        except Exception as e:
            print(f"❌ 统一FPS配置测试失败: {e}")
            return False
    
    def test_network_sync_optimization(self):
        """测试网络同步优化"""
        print("🌐 测试网络同步优化...")
        
        try:
            # 创建高性能配置
            fps_config = FPSConfig("high_performance")
            sync_optimizer = NetworkSyncOptimizer(fps_config)
            
            # 测试同步频率
            current_time = time.time()
            
            # 第一次应该同步
            should_sync1 = sync_optimizer.should_sync(current_time)
            assert should_sync1 == True, "首次同步判断错误"
            
            # 立即再次检查，不应该同步
            should_sync2 = sync_optimizer.should_sync(current_time)
            assert should_sync2 == False, "同步频率控制错误"
            
            # 等待足够时间后应该同步
            future_time = current_time + fps_config.network_interval + 0.001
            should_sync3 = sync_optimizer.should_sync(future_time)
            assert should_sync3 == True, "延迟同步判断错误"
            
            # 测试数据优化
            test_game_state = {
                "tanks": [
                    {"id": "host", "x": 123.456789, "y": 234.567890, "angle": 45.123456, "health": 100, "alive": True},
                    {"id": "client", "x": 345.678901, "y": 456.789012, "angle": 90.654321, "health": 80, "alive": True}
                ],
                "bullets": [
                    {"id": "bullet1", "x": 100.123456, "y": 200.234567, "angle": 0.123456, "owner": "host"}
                ],
                "round_info": {"score": [1, 0]}
            }
            
            optimized_state = sync_optimizer.optimize_sync_data(test_game_state)
            
            # 验证数据优化
            assert "tanks" in optimized_state, "优化后状态缺少tanks"
            assert "bullets" in optimized_state, "优化后状态缺少bullets"
            assert len(optimized_state["tanks"]) == 2, "坦克数量不正确"
            
            # 验证精度优化
            tank = optimized_state["tanks"][0]
            assert tank["x"] == 123.5, f"X坐标精度优化错误: {tank['x']}"
            assert tank["y"] == 234.6, f"Y坐标精度优化错误: {tank['y']}"
            
            print("✅ 网络同步优化测试通过")
            return True
            
        except Exception as e:
            print(f"❌ 网络同步优化测试失败: {e}")
            return False
    
    def test_multiplayer_sync_consistency(self):
        """测试多人游戏同步一致性"""
        print("🎮 测试多人游戏同步一致性...")
        
        try:
            # 设置高性能模式
            fps_config = set_fps_config("high_performance")
            
            # 创建主机和客户端
            host = GameHost(host_port=12355)  # 使用不同端口避免冲突
            client = GameClient()
            
            # 设置回调
            sync_events = []
            
            def on_game_state(state):
                sync_events.append({
                    "timestamp": time.time(),
                    "tanks": len(state.get("tanks", [])),
                    "bullets": len(state.get("bullets", []))
                })
            
            client.set_callbacks(game_state=on_game_state)
            
            # 启动主机
            success = host.start_hosting("同步测试房间", "测试主机")
            assert success, "主机启动失败"
            
            time.sleep(0.2)
            
            # 客户端连接
            success = client.connect_to_host("127.0.0.1", 12355, "测试客户端")
            assert success, "客户端连接失败"
            
            time.sleep(0.5)
            
            # 模拟游戏状态同步
            test_state = {
                "tanks": [{"id": "host", "x": 100, "y": 100}],
                "bullets": [],
                "round_info": {}
            }
            
            # 发送多次状态更新
            start_time = time.time()
            for i in range(10):
                test_state["tanks"][0]["x"] = 100 + i * 10
                host.send_game_state(test_state)
                time.sleep(1.0 / fps_config.network_sync_fps)  # 按配置的同步频率发送
            
            time.sleep(0.5)  # 等待最后的同步
            
            # 验证同步频率
            if len(sync_events) >= 2:
                time_intervals = []
                for i in range(1, len(sync_events)):
                    interval = sync_events[i]["timestamp"] - sync_events[i-1]["timestamp"]
                    time_intervals.append(interval)
                
                avg_interval = sum(time_intervals) / len(time_intervals)
                expected_interval = 1.0 / fps_config.network_sync_fps
                
                # 允许10%的误差
                tolerance = expected_interval * 0.1
                assert abs(avg_interval - expected_interval) < tolerance, \
                    f"同步间隔不符合预期: {avg_interval:.3f}s vs {expected_interval:.3f}s"
                
                print(f"   同步频率验证: 平均间隔 {avg_interval:.3f}s, 预期 {expected_interval:.3f}s")
            
            # 清理
            client.disconnect()
            host.stop_hosting()
            time.sleep(0.2)
            
            print("✅ 多人游戏同步一致性测试通过")
            return True
            
        except Exception as e:
            print(f"❌ 多人游戏同步一致性测试失败: {e}")
            # 确保清理
            try:
                client.disconnect()
                host.stop_hosting()
            except:
                pass
            return False
    
    def test_performance_impact(self):
        """测试性能影响"""
        print("⚡ 测试性能影响...")
        
        try:
            fps_config = FPSConfig("high_performance")
            sync_optimizer = NetworkSyncOptimizer(fps_config)
            
            # 创建大量测试数据
            large_game_state = {
                "tanks": [
                    {"id": f"tank_{i}", "x": i * 10, "y": i * 10, "angle": i, "health": 100, "alive": True}
                    for i in range(50)  # 50个坦克
                ],
                "bullets": [
                    {"id": f"bullet_{i}", "x": i * 5, "y": i * 5, "angle": i * 2, "owner": f"tank_{i%10}"}
                    for i in range(100)  # 100个子弹
                ],
                "round_info": {"score": [5, 3]}
            }
            
            # 性能测试
            iterations = 1000
            
            # 测试同步判断性能
            start_time = time.time()
            current_time = time.time()
            for i in range(iterations):
                sync_optimizer.should_sync(current_time + i * 0.001)
            sync_time = time.time() - start_time
            
            # 测试数据优化性能
            start_time = time.time()
            for _ in range(iterations // 10):  # 减少迭代次数，因为数据优化更复杂
                sync_optimizer.optimize_sync_data(large_game_state)
            optimize_time = time.time() - start_time
            
            # 性能评估
            sync_avg_time = sync_time / iterations * 1000  # 毫秒
            optimize_avg_time = optimize_time / (iterations // 10) * 1000  # 毫秒
            
            print(f"   同步判断平均耗时: {sync_avg_time:.3f}ms")
            print(f"   数据优化平均耗时: {optimize_avg_time:.3f}ms")
            
            # 性能要求
            assert sync_avg_time < 0.1, f"同步判断性能不达标: {sync_avg_time:.3f}ms"
            assert optimize_avg_time < 5.0, f"数据优化性能不达标: {optimize_avg_time:.3f}ms"
            
            print("✅ 性能影响测试通过")
            return True
            
        except Exception as e:
            print(f"❌ 性能影响测试失败: {e}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🧪 开始FPS同步集成测试")
        print("=" * 60)
        
        tests = [
            ("统一FPS配置", self.test_unified_fps_config),
            ("网络同步优化", self.test_network_sync_optimization),
            ("多人游戏同步一致性", self.test_multiplayer_sync_consistency),
            ("性能影响", self.test_performance_impact),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n📋 {test_name}测试:")
            if test_func():
                passed += 1
                self.test_results[test_name] = "通过"
            else:
                self.test_results[test_name] = "失败"
        
        print("\n" + "=" * 60)
        print(f"🎉 测试完成: {passed}/{total} 通过")
        
        if passed == total:
            print("✅ 所有测试通过！FPS同步修复方案已成功集成。")
            print("\n📊 修复效果:")
            print("   • 主机端和客户端刷新率统一为60FPS")
            print("   • 网络同步频率提升到60FPS")
            print("   • 物理更新频率保持60FPS")
            print("   • 数据传输经过优化，减少网络负载")
            print("   • 性能影响在可接受范围内")
        else:
            print("❌ 部分测试失败，需要进一步调试。")
        
        return passed == total


def main():
    """主测试函数"""
    print("🎮 多人联机FPS同步修复集成测试")
    print("测试目标：验证主机端和客户端刷新率同步修复的完整效果")
    print()
    
    # 运行测试
    test_suite = FPSSyncIntegrationTest()
    success = test_suite.run_all_tests()
    
    print("\n📊 测试结果总结:")
    for test_name, result in test_suite.test_results.items():
        status = "✅" if result == "通过" else "❌"
        print(f"   {status} {test_name}: {result}")
    
    if success:
        print("\n🎯 修复方案验证成功！")
        print("现在可以启动游戏体验同步的60FPS多人联机效果。")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
