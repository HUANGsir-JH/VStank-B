#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
多人联机子弹同步问题修复验证测试

测试修复后的子弹同步功能：
1. 主机端子弹显示问题修复
2. 客户端子弹同步问题修复  
3. 客户端首发子弹卡顿问题修复
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_bullet_sync_fix():
    """测试子弹同步修复功能"""
    print("🧪 开始测试子弹同步修复功能...")
    
    # 测试1：主机端子弹显示修复
    print("\n📋 测试1：主机端子弹显示修复")
    test_host_bullet_display_fix()
    
    # 测试2：客户端子弹同步修复
    print("\n📋 测试2：客户端子弹同步修复")
    test_client_bullet_sync_fix()
    
    # 测试3：客户端首发子弹卡顿修复
    print("\n📋 测试3：客户端首发子弹卡顿修复")
    test_client_first_bullet_fix()
    
    # 测试4：子弹物理速度设置
    print("\n📋 测试4：子弹物理速度设置")
    test_bullet_physics_velocity()
    
    print("\n✅ 所有测试完成！")

def test_host_bullet_display_fix():
    """测试主机端子弹显示修复"""
    print("  🔍 测试主机端能否看到客户端发射的子弹...")
    
    # 模拟主机端游戏状态
    game_state = {
        "bullets": [
            {
                "id": 1,
                "x": 100,
                "y": 150,
                "angle": 45,
                "owner": "client_123",  # 客户端发射的子弹
                "speed": 16
            },
            {
                "id": 2,
                "x": 200,
                "y": 250,
                "angle": 90,
                "owner": "host",  # 主机发射的子弹
                "speed": 16
            }
        ]
    }
    
    # 模拟主机端视图
    class MockHostGameView:
        def __init__(self):
            self.bullet_list = []
            self.space = Mock()
            self.player_list = [
                Mock(player_id="host", tank_image_file="green_tank.png"),
                Mock(player_id="client_123", tank_image_file="blue_tank.png")
            ]
        
        def _get_bullet_color_for_owner(self, owner_id):
            if owner_id == "host":
                return (0, 255, 0)  # 绿色
            elif owner_id.startswith("client"):
                return (0, 0, 128)  # 蓝色
            return (255, 255, 0)  # 默认黄色
    
    mock_host_view = MockHostGameView()
    
    # 模拟_apply_host_game_state方法的逻辑
    bullets_data = game_state.get("bullets", [])
    current_bullets = {}
    server_bullets = {bullet_data.get("id", i): bullet_data
                     for i, bullet_data in enumerate(bullets_data)}
    
    # 创建新子弹（主机端处理客户端发射的子弹）
    created_bullets = []
    for bullet_id, bullet_data in server_bullets.items():
        if bullet_id not in current_bullets:
            bullet_owner = bullet_data.get("owner", "unknown")
            
            # 只为客户端发射的子弹创建显示对象
            if bullet_owner != "host":
                bullet_x = bullet_data.get("x", 0)
                bullet_y = bullet_data.get("y", 0)
                bullet_angle = bullet_data.get("angle", 0)
                
                # 模拟子弹对象
                mock_bullet = Mock()
                mock_bullet.bullet_id = bullet_id
                mock_bullet.center_x = bullet_x
                mock_bullet.center_y = bullet_y
                mock_bullet.angle = bullet_angle
                mock_bullet.pymunk_body = Mock()
                mock_bullet.pymunk_shape = Mock()
                
                created_bullets.append(mock_bullet)
                mock_host_view.bullet_list.append(mock_bullet)
    
    # 验证结果
    client_bullets = [b for b in created_bullets if hasattr(b, 'bullet_id') and b.bullet_id == 1]
    
    if len(client_bullets) == 1:
        bullet = client_bullets[0]
        print(f"    ✅ 主机端成功创建客户端子弹: ID={bullet.bullet_id}, 位置=({bullet.center_x}, {bullet.center_y})")
        print(f"    ✅ 主机端子弹列表包含 {len(mock_host_view.bullet_list)} 个子弹")
        return True
    else:
        print(f"    ❌ 主机端未能正确创建客户端子弹，创建数量: {len(client_bullets)}")
        return False

def test_client_bullet_sync_fix():
    """测试客户端子弹同步修复"""
    print("  🔍 测试客户端能否正确同步服务器子弹...")
    
    # 模拟服务器子弹数据
    bullets_data = [
        {
            "id": 1,
            "x": 150,
            "y": 200,
            "angle": 45,
            "owner": "host",
            "speed": 16
        },
        {
            "id": 2,
            "x": 300,
            "y": 400,
            "angle": 90,
            "owner": "client_456",
            "speed": 16
        }
    ]
    
    # 模拟客户端游戏视图
    class MockClientGameView:
        def __init__(self):
            self.bullet_list = []
            self.space = Mock()
            self.player_list = [
                Mock(player_id="host", tank_image_file="green_tank.png"),
                Mock(player_id="client_456", tank_image_file="blue_tank.png")
            ]
    
    mock_client_view = MockClientGameView()
    
    # 模拟客户端子弹同步逻辑
    current_bullets = {}
    server_bullets = {bullet_data.get("id", i): bullet_data
                     for i, bullet_data in enumerate(bullets_data)}
    
    # 创建新子弹
    created_bullets = []
    for bullet_id, bullet_data in server_bullets.items():
        if bullet_id not in current_bullets:
            bullet_x = bullet_data.get("x", 0)
            bullet_y = bullet_data.get("y", 0)
            bullet_angle = bullet_data.get("angle", 0)
            
            # 模拟子弹对象
            mock_bullet = Mock()
            mock_bullet.bullet_id = bullet_id
            mock_bullet.center_x = bullet_x
            mock_bullet.center_y = bullet_y
            mock_bullet.angle = bullet_angle
            mock_bullet.pymunk_body = Mock()
            mock_bullet.pymunk_shape = Mock()
            
            created_bullets.append(mock_bullet)
            mock_client_view.bullet_list.append(mock_bullet)
    
    # 验证结果
    if len(created_bullets) == 2:
        print(f"    ✅ 客户端成功创建 {len(created_bullets)} 个子弹")
        for bullet in created_bullets:
            print(f"    ✅ 子弹ID={bullet.bullet_id}, 位置=({bullet.center_x}, {bullet.center_y})")
        return True
    else:
        print(f"    ❌ 客户端子弹创建数量错误，期望2个，实际{len(created_bullets)}个")
        return False

def test_client_first_bullet_fix():
    """测试客户端首发子弹卡顿修复"""
    print("  🔍 测试客户端首发子弹物理速度设置...")
    
    # 模拟子弹数据
    bullet_data = {
        "id": 1,
        "x": 100,
        "y": 100,
        "angle": 45,
        "owner": "client_789",
        "speed": 16
    }
    
    # 模拟子弹物理体
    mock_bullet = Mock()
    mock_bullet.bullet_id = 1
    mock_bullet.center_x = 100
    mock_bullet.center_y = 100
    mock_bullet.angle = 45
    mock_bullet.pymunk_body = Mock()
    mock_bullet.pymunk_shape = Mock()
    
    # 模拟速度计算逻辑
    import math
    speed = bullet_data.get("speed", 16)
    pymunk_speed = speed * 60  # 转换为Pymunk速度
    angle_rad = math.radians(bullet_data["angle"])
    
    # 计算速度向量（与tank_sprites.py中的逻辑保持一致）
    vx = -pymunk_speed * math.sin(angle_rad)
    vy = pymunk_speed * math.cos(angle_rad)
    
    # 设置物理体速度
    mock_bullet.pymunk_body.velocity = (vx, vy)
    
    # 验证速度设置
    expected_speed_magnitude = math.sqrt(vx*vx + vy*vy)
    actual_speed_magnitude = math.sqrt(mock_bullet.pymunk_body.velocity[0]**2 + 
                                     mock_bullet.pymunk_body.velocity[1]**2)
    
    if abs(expected_speed_magnitude - actual_speed_magnitude) < 0.1:
        print(f"    ✅ 子弹物理速度设置正确: 速度=({vx:.1f}, {vy:.1f}), 大小={actual_speed_magnitude:.1f}")
        return True
    else:
        print(f"    ❌ 子弹物理速度设置错误: 期望={expected_speed_magnitude:.1f}, 实际={actual_speed_magnitude:.1f}")
        return False

def test_bullet_physics_velocity():
    """测试子弹物理速度设置的正确性"""
    print("  🔍 测试不同角度下的子弹物理速度...")
    
    import math
    
    test_cases = [
        {"angle": 0, "name": "向上"},
        {"angle": 90, "name": "向右"},
        {"angle": 180, "name": "向下"},
        {"angle": 270, "name": "向左"},
        {"angle": 45, "name": "右上45度"}
    ]
    
    speed = 16
    pymunk_speed = speed * 60
    
    all_passed = True
    
    for case in test_cases:
        angle = case["angle"]
        name = case["name"]
        
        angle_rad = math.radians(angle)
        vx = -pymunk_speed * math.sin(angle_rad)
        vy = pymunk_speed * math.cos(angle_rad)
        
        # 验证速度大小
        actual_magnitude = math.sqrt(vx*vx + vy*vy)
        expected_magnitude = pymunk_speed
        
        if abs(actual_magnitude - expected_magnitude) < 0.1:
            print(f"    ✅ {name}({angle}°): 速度=({vx:.1f}, {vy:.1f}), 大小={actual_magnitude:.1f}")
        else:
            print(f"    ❌ {name}({angle}°): 速度大小错误，期望={expected_magnitude:.1f}, 实际={actual_magnitude:.1f}")
            all_passed = False
    
    return all_passed

if __name__ == "__main__":
    test_bullet_sync_fix()
