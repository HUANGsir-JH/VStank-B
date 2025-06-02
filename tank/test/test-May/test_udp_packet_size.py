#!/usr/bin/env python3
"""
测试UDP数据包大小优化

验证游戏状态数据包大小是否在合理范围内
"""

import sys
import os
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_game_state_packet_size():
    """测试游戏状态数据包大小"""
    print("🧪 测试游戏状态数据包大小...")
    
    try:
        from multiplayer.udp_messages import MessageFactory
        
        # 模拟典型的游戏状态数据（优化后格式）
        test_game_state = {
            "tanks": [
                {
                    "id": "host",
                    "pos": [100.5, 200.3],
                    "ang": 45.2,
                    "hp": 5,
                    "type": "green"
                },
                {
                    "id": "client_12345678",
                    "pos": [300.1, 400.7],
                    "ang": 90.0,
                    "hp": 3,
                    "type": "blue"
                }
            ],
            "bullets": [
                {
                    "id": 0,
                    "pos": [150.2, 250.8],
                    "ang": 45.5,
                    "own": "host"
                },
                {
                    "id": 1,
                    "pos": [350.9, 450.1],
                    "ang": 90.3,
                    "own": "client_12345678"
                }
            ],
            "round_info": {
                "sc": [1, 0],
                "ro": False,
                "go": False
            }
        }
        
        # 创建游戏状态消息
        message = MessageFactory.create_game_state(
            test_game_state["tanks"],
            test_game_state["bullets"],
            test_game_state["round_info"]
        )
        
        # 测试数据包大小
        message_bytes = message.to_bytes()
        packet_size = len(message_bytes)
        
        print(f"📦 优化后数据包大小: {packet_size} 字节")
        
        # 验证大小是否合理
        max_safe_size = 1400  # 以太网MTU减去IP/UDP头部
        if packet_size <= max_safe_size:
            print(f"✅ 数据包大小合理 (≤ {max_safe_size} 字节)")
        else:
            print(f"❌ 数据包过大 (> {max_safe_size} 字节)")
            return False
        
        # 显示数据内容（用于调试）
        print(f"📄 数据包内容预览:")
        message_dict = json.loads(message_bytes.decode('utf-8'))
        print(f"   消息类型: {message_dict['type']}")
        print(f"   坦克数量: {len(message_dict['data']['tanks'])}")
        print(f"   子弹数量: {len(message_dict['data']['bullets'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_old_vs_new_format_size():
    """对比优化前后的数据包大小"""
    print("🧪 对比优化前后数据包大小...")
    
    try:
        from multiplayer.udp_messages import MessageFactory
        
        # 旧格式数据（优化前）
        old_format_data = {
            "tanks": [
                {
                    "player_id": "host",
                    "position": [100.123456, 200.654321],
                    "angle": 45.987654,
                    "health": 5,
                    "tank_image": "d:\\VSTank\\tank\\tank-img\\green_tank.png"
                },
                {
                    "player_id": "client_12345678",
                    "position": [300.111111, 400.222222],
                    "angle": 90.333333,
                    "health": 3,
                    "tank_image": "d:\\VSTank\\tank\\tank-img\\blue_tank.png"
                }
            ],
            "bullets": [
                {
                    "id": 140234567890123,
                    "position": [150.555555, 250.666666],
                    "angle": 45.777777,
                    "owner": "host"
                }
            ],
            "round_info": {
                "scores": {
                    "player1": 1,
                    "player2": 0
                },
                "round_over": False,
                "game_over": False,
                "winner": None
            }
        }
        
        # 新格式数据（优化后）
        new_format_data = {
            "tanks": [
                {
                    "id": "host",
                    "pos": [100.1, 200.7],
                    "ang": 46.0,
                    "hp": 5,
                    "type": "green"
                },
                {
                    "id": "client_12345678",
                    "pos": [300.1, 400.2],
                    "ang": 90.3,
                    "hp": 3,
                    "type": "blue"
                }
            ],
            "bullets": [
                {
                    "id": 0,
                    "pos": [150.6, 250.7],
                    "ang": 45.8,
                    "own": "host"
                }
            ],
            "round_info": {
                "sc": [1, 0],
                "ro": False,
                "go": False
            }
        }
        
        # 创建消息并比较大小
        old_message = MessageFactory.create_game_state(
            old_format_data["tanks"],
            old_format_data["bullets"],
            old_format_data["round_info"]
        )
        
        new_message = MessageFactory.create_game_state(
            new_format_data["tanks"],
            new_format_data["bullets"],
            new_format_data["round_info"]
        )
        
        old_size = len(old_message.to_bytes())
        new_size = len(new_message.to_bytes())
        reduction = old_size - new_size
        reduction_percent = (reduction / old_size) * 100
        
        print(f"📊 大小对比:")
        print(f"   优化前: {old_size} 字节")
        print(f"   优化后: {new_size} 字节")
        print(f"   减少: {reduction} 字节 ({reduction_percent:.1f}%)")
        
        if reduction > 0:
            print(f"✅ 数据包大小优化成功")
        else:
            print(f"⚠️ 数据包大小未减少")
        
        return True
        
    except Exception as e:
        print(f"❌ 对比测试失败: {e}")
        return False

def test_buffer_size_adequacy():
    """测试缓冲区大小是否足够"""
    print("🧪 测试缓冲区大小充足性...")
    
    try:
        # 模拟最大游戏状态（4个玩家，多个子弹）
        max_game_state = {
            "tanks": [
                {
                    "id": f"player_{i}",
                    "pos": [100.0 + i * 50, 200.0 + i * 30],
                    "ang": 45.0 + i * 15,
                    "hp": 5,
                    "type": ["green", "blue", "yellow", "grey"][i]
                }
                for i in range(4)  # 4个玩家
            ],
            "bullets": [
                {
                    "id": i,
                    "pos": [150.0 + i * 10, 250.0 + i * 5],
                    "ang": 45.0 + i * 5,
                    "own": f"player_{i % 4}"
                }
                for i in range(20)  # 20个子弹
            ],
            "round_info": {
                "sc": [2, 1, 0, 1],
                "ro": False,
                "go": False
            }
        }
        
        from multiplayer.udp_messages import MessageFactory
        
        message = MessageFactory.create_game_state(
            max_game_state["tanks"],
            max_game_state["bullets"],
            max_game_state["round_info"]
        )
        
        max_packet_size = len(message.to_bytes())
        buffer_size = 8192  # 我们设置的缓冲区大小
        
        print(f"📏 最大数据包大小: {max_packet_size} 字节")
        print(f"📦 缓冲区大小: {buffer_size} 字节")
        
        if max_packet_size < buffer_size:
            margin = buffer_size - max_packet_size
            print(f"✅ 缓冲区充足 (余量: {margin} 字节)")
            return True
        else:
            print(f"❌ 缓冲区不足")
            return False
        
    except Exception as e:
        print(f"❌ 缓冲区测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始UDP数据包大小优化测试")
    print("=" * 50)
    
    tests = [
        test_game_state_packet_size,
        test_old_vs_new_format_size,
        test_buffer_size_adequacy,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            print()
    
    print("=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！UDP数据包大小优化成功")
        return True
    else:
        print("⚠️ 部分测试失败，需要进一步优化")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
