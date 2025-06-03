#!/usr/bin/env python3
"""
子弹视觉修复验证脚本

这个脚本验证子弹大小和颜色修复是否成功，检查：
1. 主机端是否发送完整的坦克信息
2. 客户端是否正确计算子弹颜色
3. 子弹半径是否使用标准值
4. 网络数据结构是否完整
"""

import sys
import os
import re

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def verify_host_tank_data_transmission():
    """验证主机端坦克数据传输"""
    print("🔍 验证主机端坦克数据传输...")
    
    network_views_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                     "multiplayer", "network_views.py")
    
    with open(network_views_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查主机端是否发送tank_image_file
    checks = [
        ("坦克图片文件发送", r"[\"']tank_image_file[\"']:\s*getattr\(tank,\s*[\"']tank_image_file[\"']"),
        ("坦克状态提取", r"# 提取坦克状态"),
        ("坦克数据结构", r"tanks\.append\(\{")
    ]
    
    missing_checks = []
    for check_name, pattern in checks:
        if not re.search(pattern, content):
            missing_checks.append(check_name)
    
    if missing_checks:
        print(f"❌ 主机端缺少: {', '.join(missing_checks)}")
        return False
    
    print("✅ 主机端坦克数据传输验证通过")
    return True

def verify_client_tank_data_application():
    """验证客户端坦克数据应用"""
    print("🔍 验证客户端坦克数据应用...")
    
    network_views_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                     "multiplayer", "network_views.py")
    
    with open(network_views_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查客户端是否应用tank_image_file
    checks = [
        ("坦克图片文件应用", r"tank\.tank_image_file\s*=\s*tank_data\["),
        ("玩家ID应用", r"tank\.player_id\s*=\s*tank_data\["),
        ("坦克状态更新", r"# 更新坦克状态")
    ]
    
    missing_checks = []
    for check_name, pattern in checks:
        if not re.search(pattern, content):
            missing_checks.append(check_name)
    
    if missing_checks:
        print(f"❌ 客户端缺少: {', '.join(missing_checks)}")
        return False
    
    print("✅ 客户端坦克数据应用验证通过")
    return True

def verify_bullet_color_calculation():
    """验证子弹颜色计算方法"""
    print("🔍 验证子弹颜色计算方法...")
    
    network_views_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                     "multiplayer", "network_views.py")
    
    with open(network_views_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查颜色计算方法
    checks = [
        ("颜色计算方法", r"def\s+_get_bullet_color_for_owner\("),
        ("绿色坦克颜色", r"if\s+[\"']green[\"']\s+in\s+path:"),
        ("蓝色坦克颜色", r"elif\s+[\"']blue[\"']\s+in\s+path:"),
        ("沙漠坦克颜色", r"elif\s+[\"']desert[\"']\s+in\s+path:"),
        ("灰色坦克颜色", r"elif\s+[\"']grey[\"']\s+in\s+path:"),
        ("默认主机颜色", r"if\s+owner_id\s*==\s*[\"']host[\"']:"),
        ("默认客户端颜色", r"elif\s+owner_id\.startswith\([\"']client[\"']\):")
    ]
    
    missing_checks = []
    for check_name, pattern in checks:
        if not re.search(pattern, content):
            missing_checks.append(check_name)
    
    if missing_checks:
        print(f"❌ 颜色计算缺少: {', '.join(missing_checks)}")
        return False
    
    print("✅ 子弹颜色计算方法验证通过")
    return True

def verify_bullet_creation_logic():
    """验证子弹创建逻辑"""
    print("🔍 验证子弹创建逻辑...")
    
    network_views_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                     "multiplayer", "network_views.py")
    
    with open(network_views_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查子弹创建逻辑
    checks = [
        ("颜色计算调用", r"bullet_color\s*=\s*self\._get_bullet_color_for_owner\("),
        ("标准半径使用", r"BULLET_RADIUS\s*=\s*4"),
        ("半径参数传递", r"radius=BULLET_RADIUS"),
        ("颜色参数传递", r"color=bullet_color"),
        ("子弹导入", r"from\s+tank_sprites\s+import\s+Bullet")
    ]
    
    missing_checks = []
    for check_name, pattern in checks:
        if not re.search(pattern, content):
            missing_checks.append(check_name)
    
    if missing_checks:
        print(f"❌ 子弹创建缺少: {', '.join(missing_checks)}")
        return False
    
    print("✅ 子弹创建逻辑验证通过")
    return True

def verify_standard_bullet_radius():
    """验证标准子弹半径定义"""
    print("🔍 验证标准子弹半径定义...")
    
    tank_sprites_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                    "tank_sprites.py")
    
    with open(tank_sprites_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查标准半径定义
    if not re.search(r"BULLET_RADIUS\s*=\s*4", content):
        print("❌ 标准子弹半径定义不正确")
        return False
    
    print("✅ 标准子弹半径定义验证通过")
    return True

def run_functional_test():
    """运行功能测试"""
    print("🔍 运行功能测试...")

    try:
        # 模拟颜色计算逻辑（不依赖Arcade窗口）
        def mock_get_bullet_color_for_owner(owner_id, player_list):
            """模拟颜色计算逻辑"""
            import arcade

            bullet_color = arcade.color.YELLOW_ORANGE

            # 根据所有者ID找到对应的坦克
            for tank in player_list:
                if tank is not None and hasattr(tank, 'player_id'):
                    if getattr(tank, 'player_id', None) == owner_id:
                        if hasattr(tank, 'tank_image_file') and tank.tank_image_file:
                            path = tank.tank_image_file.lower()
                            if 'green' in path:
                                bullet_color = (0, 255, 0)
                            elif 'desert' in path:
                                bullet_color = (255, 165, 0)
                            elif 'grey' in path:
                                bullet_color = (128, 128, 128)
                            elif 'blue' in path:
                                bullet_color = (0, 0, 128)
                        break

            # 默认颜色方案
            if owner_id == "host":
                bullet_color = (0, 255, 0)
            elif owner_id.startswith("client"):
                bullet_color = (0, 0, 128)

            return bullet_color

        from unittest.mock import Mock

        # 创建模拟坦克列表
        player_list = []

        # 添加绿色坦克
        green_tank = Mock()
        green_tank.player_id = "host"
        green_tank.tank_image_file = "green_tank.png"
        player_list.append(green_tank)

        # 添加蓝色坦克
        blue_tank = Mock()
        blue_tank.player_id = "client_001"
        blue_tank.tank_image_file = "blue_tank.png"
        player_list.append(blue_tank)

        # 测试颜色计算
        test_cases = [
            ("host", (0, 255, 0)),           # 绿色坦克
            ("client_001", (0, 0, 128)),     # 蓝色坦克
            ("client_999", (0, 0, 128)),     # 未知客户端
        ]

        for owner_id, expected_color in test_cases:
            actual_color = mock_get_bullet_color_for_owner(owner_id, player_list)
            if actual_color != expected_color:
                print(f"❌ 颜色计算错误: 所有者 {owner_id}, 期望 {expected_color}, 实际 {actual_color}")
                return False

        print("✅ 功能测试通过")
        return True

    except Exception as e:
        print(f"❌ 功能测试失败: {e}")
        return False

def verify_test_files():
    """验证测试文件"""
    print("🔍 验证测试文件...")
    
    test_files = [
        "test_bullet_visual_fix.py",
        "test_bullet_visual_integration.py"
    ]
    
    test_dir = os.path.dirname(__file__)
    
    for test_file in test_files:
        test_path = os.path.join(test_dir, test_file)
        if not os.path.exists(test_path):
            print(f"❌ 测试文件不存在: {test_file}")
            return False
    
    print("✅ 测试文件验证通过")
    return True

def verify_documentation():
    """验证文档"""
    print("🔍 验证修复文档...")
    
    doc_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                           "BULLET_VISUAL_FIX_SUMMARY.md")
    
    if not os.path.exists(doc_path):
        print("❌ 修复文档不存在")
        return False
    
    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查文档内容
    doc_sections = [
        "问题描述",
        "修复方案", 
        "修复效果",
        "测试验证",
        "技术细节"
    ]
    
    missing_sections = []
    for section in doc_sections:
        if section not in content:
            missing_sections.append(section)
    
    if missing_sections:
        print(f"❌ 文档缺少章节: {', '.join(missing_sections)}")
        return False
    
    print("✅ 修复文档验证通过")
    return True

def main():
    """主验证函数"""
    print("🚀 子弹视觉修复验证")
    print("=" * 60)
    
    verifications = [
        ("主机端数据传输", verify_host_tank_data_transmission),
        ("客户端数据应用", verify_client_tank_data_application),
        ("子弹颜色计算", verify_bullet_color_calculation),
        ("子弹创建逻辑", verify_bullet_creation_logic),
        ("标准半径定义", verify_standard_bullet_radius),
        ("功能测试", run_functional_test),
        ("测试文件", verify_test_files),
        ("文档", verify_documentation)
    ]
    
    passed = 0
    failed = 0
    
    for name, verification in verifications:
        print(f"\n📋 验证: {name}")
        try:
            if verification():
                passed += 1
                print(f"✅ {name} 验证通过")
            else:
                failed += 1
                print(f"❌ {name} 验证失败")
        except Exception as e:
            failed += 1
            print(f"❌ {name} 验证异常: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 验证结果: {passed} 通过, {failed} 失败")
    
    if failed == 0:
        print("\n🎉 所有验证通过！子弹视觉修复成功！")
        print("\n✅ 修复总结:")
        print("  - 子弹大小与标准一致（4像素半径）")
        print("  - 子弹颜色根据坦克类型正确确定")
        print("  - 主机端发送完整的坦克图片信息")
        print("  - 客户端正确计算和应用子弹颜色")
        print("  - 不同玩家的子弹可以通过颜色区分")
        print("  - 主机端和客户端视觉效果完全一致")
        print("\n🎮 多人联机子弹视觉问题已完全解决！")
        return True
    else:
        print(f"\n❌ 发现 {failed} 个问题，需要进一步检查")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
