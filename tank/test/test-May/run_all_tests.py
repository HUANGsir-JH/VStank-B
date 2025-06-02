"""
综合测试运行器

运行所有测试套件的主程序
"""

import sys
import os
import time
import argparse

# 添加父目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_multiplayer import MultiplayerTestSuite
from test_network import NetworkTestSuite
from test_game_logic import GameLogicTestSuite

# 导入OpenGL修复测试
try:
    from test_opengl_fix import main as run_opengl_fix_test
    OPENGL_FIX_TEST_AVAILABLE = True
except ImportError:
    OPENGL_FIX_TEST_AVAILABLE = False


class TestRunner:
    """测试运行器"""

    def __init__(self):
        self.all_results = []
        self.start_time = None
        self.end_time = None

    def run_all_tests(self, include_network=True, include_multiplayer=True, include_game_logic=True, include_opengl_fix=True):
        """运行所有测试套件"""
        print("🚀 坦克动荡 - 综合测试套件")
        print("=" * 60)
        print(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        self.start_time = time.time()

        # 测试套件列表
        test_suites = []

        if include_game_logic:
            test_suites.append(("游戏逻辑", GameLogicTestSuite))

        if include_multiplayer:
            test_suites.append(("多人游戏", MultiplayerTestSuite))

        if include_network:
            test_suites.append(("网络功能", NetworkTestSuite))

        # 添加OpenGL修复测试
        if include_opengl_fix and OPENGL_FIX_TEST_AVAILABLE:
            test_suites.append(("OpenGL修复", None))  # 特殊处理

        # 运行每个测试套件
        for suite_name, suite_class in test_suites:
            print(f"🧪 运行 {suite_name} 测试套件")
            print("-" * 40)

            try:
                if suite_name == "OpenGL修复":
                    # 特殊处理OpenGL修复测试
                    from test_opengl_fix import main as run_opengl_fix_test
                    success = run_opengl_fix_test()
                    if success:
                        self.all_results.append((suite_name, 2, 2, [("线程安全测试", "PASS", ""), ("精灵创建测试", "PASS", "")]))
                        print(f"✅ {suite_name} 测试套件完成: 2/2 通过")
                    else:
                        self.all_results.append((suite_name, 0, 2, [("线程安全测试", "FAIL", "测试失败"), ("精灵创建测试", "FAIL", "测试失败")]))
                        print(f"❌ {suite_name} 测试套件完成: 0/2 通过")
                else:
                    # 常规测试套件
                    suite = suite_class()
                    suite.run_all_tests()

                    # 收集结果
                    passed = sum(1 for _, status, _ in suite.test_results if status == "PASS")
                    total = len(suite.test_results)
                    self.all_results.append((suite_name, passed, total, suite.test_results))

                    print(f"✅ {suite_name} 测试套件完成: {passed}/{total} 通过")

            except Exception as e:
                print(f"❌ {suite_name} 测试套件失败: {e}")
                self.all_results.append((suite_name, 0, 0, []))
                import traceback
                traceback.print_exc()

            print()

        self.end_time = time.time()
        self.print_final_summary()

    def print_final_summary(self):
        """打印最终测试摘要"""
        print("=" * 60)
        print("🏁 最终测试摘要")
        print("=" * 60)

        total_passed = 0
        total_tests = 0

        for suite_name, passed, total, results in self.all_results:
            total_passed += passed
            total_tests += total

            if total > 0:
                percentage = (passed / total) * 100
                status_icon = "✅" if passed == total else "⚠️" if passed > 0 else "❌"
                print(f"{status_icon} {suite_name:12} : {passed:2}/{total:2} ({percentage:5.1f}%)")
            else:
                print(f"❌ {suite_name:12} : 测试套件执行失败")

        print("-" * 40)

        if total_tests > 0:
            overall_percentage = (total_passed / total_tests) * 100
            print(f"📊 总计          : {total_passed:2}/{total_tests:2} ({overall_percentage:5.1f}%)")
        else:
            print("📊 总计          : 无测试执行")

        # 执行时间
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            print(f"⏱️  执行时间      : {duration:.2f} 秒")

        print(f"🕐 结束时间      : {time.strftime('%Y-%m-%d %H:%M:%S')}")

        # 最终状态
        print()
        if total_tests > 0 and total_passed == total_tests:
            print("🎉 所有测试都通过了！游戏系统运行正常。")
        elif total_passed > 0:
            print("⚠️  部分测试通过。请检查失败的测试项目。")
        else:
            print("❌ 测试失败。请检查系统配置和代码。")

        print()
        self.print_detailed_failures()

    def print_detailed_failures(self):
        """打印详细的失败信息"""
        has_failures = False

        for suite_name, passed, total, results in self.all_results:
            failures = [(name, result) for name, status, result in results if status == "FAIL"]

            if failures:
                if not has_failures:
                    print("🔍 失败详情:")
                    print("-" * 40)
                    has_failures = True

                print(f"\n📋 {suite_name} 测试套件失败项目:")
                for test_name, error_msg in failures:
                    print(f"   ❌ {test_name}")
                    print(f"      错误: {error_msg}")

        if not has_failures:
            print("✨ 没有失败的测试项目！")

    def run_quick_test(self):
        """运行快速测试（跳过耗时的网络测试）"""
        print("⚡ 快速测试模式")
        print("跳过部分耗时的网络测试...")
        print()

        self.run_all_tests(
            include_network=False,
            include_multiplayer=True,
            include_game_logic=True
        )

    def run_network_only(self):
        """只运行网络相关测试"""
        print("🌐 网络测试模式")
        print("只运行网络和多人游戏测试...")
        print()

        self.run_all_tests(
            include_network=True,
            include_multiplayer=True,
            include_game_logic=False
        )


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="坦克动荡游戏测试套件")
    parser.add_argument("--quick", action="store_true", help="运行快速测试（跳过耗时测试）")
    parser.add_argument("--network-only", action="store_true", help="只运行网络相关测试")
    parser.add_argument("--game-logic-only", action="store_true", help="只运行游戏逻辑测试")
    parser.add_argument("--multiplayer-only", action="store_true", help="只运行多人游戏测试")

    args = parser.parse_args()

    runner = TestRunner()

    try:
        if args.quick:
            runner.run_quick_test()
        elif args.network_only:
            runner.run_network_only()
        elif args.game_logic_only:
            runner.run_all_tests(
                include_network=False,
                include_multiplayer=False,
                include_game_logic=True
            )
        elif args.multiplayer_only:
            runner.run_all_tests(
                include_network=False,
                include_multiplayer=True,
                include_game_logic=False
            )
        else:
            runner.run_all_tests()

    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
    except Exception as e:
        print(f"\n💥 测试运行器发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
