"""
双人游戏模块测试运行器

运行所有双人游戏相关的单元测试和集成测试
"""

import unittest
import sys
import os
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def run_dual_player_tests():
    """运行所有双人游戏测试"""
    print("=" * 60)
    print("双人游戏模块测试套件")
    print("=" * 60)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试模块
    test_modules = [
        'test_dual_player_host',
        'test_dual_player_client', 
        'test_dual_player_integration'
    ]
    
    for module_name in test_modules:
        try:
            module = __import__(module_name)
            suite.addTests(loader.loadTestsFromModule(module))
            print(f"✓ 已加载测试模块: {module_name}")
        except ImportError as e:
            print(f"✗ 无法加载测试模块 {module_name}: {e}")
    
    print("-" * 60)
    
    # 运行测试
    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        descriptions=True,
        failfast=False
    )
    
    start_time = time.time()
    result = runner.run(suite)
    end_time = time.time()
    
    # 输出测试结果摘要
    print("\n" + "=" * 60)
    print("测试结果摘要")
    print("=" * 60)
    print(f"运行时间: {end_time - start_time:.2f} 秒")
    print(f"总测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    # 返回测试是否全部通过
    return len(result.failures) == 0 and len(result.errors) == 0


def run_specific_test_class(test_class_name):
    """运行特定的测试类"""
    print(f"运行测试类: {test_class_name}")
    print("-" * 40)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 根据类名加载测试
    if test_class_name == "TestClientInfo":
        from test_dual_player_host import TestClientInfo
        suite.addTests(loader.loadTestsFromTestCase(TestClientInfo))
    elif test_class_name == "TestDualPlayerHost":
        from test_dual_player_host import TestDualPlayerHost
        suite.addTests(loader.loadTestsFromTestCase(TestDualPlayerHost))
    elif test_class_name == "TestDualPlayerClient":
        from test_dual_player_client import TestDualPlayerClient
        suite.addTests(loader.loadTestsFromTestCase(TestDualPlayerClient))
    elif test_class_name == "TestDualPlayerIntegration":
        from test_dual_player_integration import TestDualPlayerIntegration
        suite.addTests(loader.loadTestsFromTestCase(TestDualPlayerIntegration))
    else:
        print(f"未知的测试类: {test_class_name}")
        return False
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return len(result.failures) == 0 and len(result.errors) == 0


def run_performance_tests():
    """运行性能相关测试"""
    print("运行性能测试...")
    print("-" * 40)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 只运行性能相关的测试
    from test_dual_player_integration import TestDualPlayerIntegration
    
    # 添加特定的性能测试方法
    suite.addTest(TestDualPlayerIntegration('test_dual_player_performance_metrics'))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return len(result.failures) == 0 and len(result.errors) == 0


def run_connection_tests():
    """运行连接相关测试"""
    print("运行连接测试...")
    print("-" * 40)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加连接相关的测试
    from test_dual_player_integration import TestDualPlayerIntegration
    from test_dual_player_client import TestDualPlayerClient
    from test_dual_player_host import TestDualPlayerHost
    
    connection_tests = [
        TestDualPlayerIntegration('test_dual_player_connection_flow'),
        TestDualPlayerIntegration('test_dual_player_disconnection_flow'),
        TestDualPlayerIntegration('test_dual_player_room_full_rejection'),
        TestDualPlayerClient('test_successful_connection'),
        TestDualPlayerClient('test_failed_connection'),
        TestDualPlayerHost('test_start_hosting_success'),
    ]
    
    for test in connection_tests:
        suite.addTest(test)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return len(result.failures) == 0 and len(result.errors) == 0


def main():
    """主函数"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "all":
            success = run_dual_player_tests()
        elif command == "performance":
            success = run_performance_tests()
        elif command == "connection":
            success = run_connection_tests()
        elif command.startswith("class:"):
            class_name = command.split(":", 1)[1]
            success = run_specific_test_class(class_name)
        else:
            print("用法:")
            print("  python run_dual_player_tests.py all              # 运行所有测试")
            print("  python run_dual_player_tests.py performance      # 运行性能测试")
            print("  python run_dual_player_tests.py connection       # 运行连接测试")
            print("  python run_dual_player_tests.py class:TestName   # 运行特定测试类")
            print("\n可用的测试类:")
            print("  - TestClientInfo")
            print("  - TestDualPlayerHost")
            print("  - TestDualPlayerClient")
            print("  - TestDualPlayerIntegration")
            return
    else:
        # 默认运行所有测试
        success = run_dual_player_tests()
    
    # 根据测试结果设置退出码
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
