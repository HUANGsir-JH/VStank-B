"""
测试Arcade API兼容性
"""

import arcade
import sys
import os

# 添加父目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_arcade_api():
    """测试Arcade API兼容性"""
    print("🎮 测试Arcade API兼容性...")
    
    # 测试可用的绘制函数
    draw_functions = [attr for attr in dir(arcade) if attr.startswith('draw_')]
    rectangle_functions = [func for func in draw_functions if 'rectangle' in func.lower()]
    
    print(f"  可用的矩形绘制函数: {rectangle_functions}")
    
    # 测试文本绘制
    text_functions = [func for func in draw_functions if 'text' in func.lower()]
    print(f"  可用的文本绘制函数: {text_functions}")
    
    # 检查特定函数是否存在
    required_functions = [
        'draw_lrbt_rectangle_filled',
        'draw_text',
        'clear'
    ]
    
    for func_name in required_functions:
        if hasattr(arcade, func_name):
            print(f"  ✅ {func_name} 可用")
        else:
            print(f"  ❌ {func_name} 不可用")
    
    print(f"  Arcade版本: {arcade.version.VERSION}")
    
    return True

if __name__ == "__main__":
    test_arcade_api()
