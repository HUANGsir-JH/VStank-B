#!/usr/bin/env python3
"""
双人联机控制修复验证测试

在单台电脑上测试主机端和客户端的坦克控制
"""

import sys
import os
import time
import threading
import subprocess
import socket

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def find_available_port():
    """查找可用端口"""
    for port in range(12340, 12400):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(('', port))
            sock.close()
            return port
        except OSError:
            continue
    raise Exception("无法找到可用端口")


def start_host_process(port):
    """启动主机进程"""
    host_script = f"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import arcade
from multiplayer.network_views import HostGameView

# 创建窗口
window = arcade.Window(800, 600, "坦克大战 - 主机端")

# 创建主机视图
host_view = HostGameView()
window.show_view(host_view)

# 启动主机
if host_view.start_hosting("测试房间", {port}):
    print("✅ 主机启动成功，端口: {port}")
    print("🎮 主机控制说明:")
    print("  WASD - 移动坦克")
    print("  空格 - 发射子弹")
    print("  ESC - 退出")
    print("\\n等待客户端连接...")
else:
    print("❌ 主机启动失败")
    sys.exit(1)

# 运行游戏
arcade.run()
"""
    
    with open("temp_host.py", "w", encoding="utf-8") as f:
        f.write(host_script)
    
    return subprocess.Popen([sys.executable, "temp_host.py"], 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE,
                          text=True)


def start_client_process(host_ip, host_port):
    """启动客户端进程"""
    client_script = f"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import arcade
from multiplayer.network_views import ClientGameView

# 创建窗口
window = arcade.Window(800, 600, "坦克大战 - 客户端")

# 创建客户端视图
client_view = ClientGameView()
window.show_view(client_view)

# 连接到主机
if client_view.connect_to_room("{host_ip}", {host_port}, "测试客户端"):
    print("✅ 客户端连接成功")
    print("🎮 客户端控制说明:")
    print("  WASD - 移动坦克")
    print("  空格 - 发射子弹")
    print("  ESC - 退出")
    print("\\n🔥 开始测试客户端控制！")
else:
    print("❌ 客户端连接失败")
    sys.exit(1)

# 运行游戏
arcade.run()
"""
    
    with open("temp_client.py", "w", encoding="utf-8") as f:
        f.write(client_script)
    
    return subprocess.Popen([sys.executable, "temp_client.py"], 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE,
                          text=True)


def cleanup_temp_files():
    """清理临时文件"""
    for filename in ["temp_host.py", "temp_client.py"]:
        try:
            if os.path.exists(filename):
                os.remove(filename)
        except:
            pass


def main():
    """主测试函数"""
    print("🚀 双人联机控制修复验证测试")
    print("=" * 50)
    
    try:
        # 查找可用端口
        port = find_available_port()
        print(f"📡 使用端口: {port}")
        
        # 启动主机进程
        print("\n🖥️ 启动主机进程...")
        host_process = start_host_process(port)
        
        # 等待主机启动
        time.sleep(3)
        
        # 检查主机是否正常启动
        if host_process.poll() is not None:
            stdout, stderr = host_process.communicate()
            print(f"❌ 主机进程异常退出:")
            print(f"stdout: {stdout}")
            print(f"stderr: {stderr}")
            return False
        
        # 启动客户端进程
        print("💻 启动客户端进程...")
        client_process = start_client_process("127.0.0.1", port)
        
        # 等待客户端连接
        time.sleep(3)
        
        # 检查客户端是否正常启动
        if client_process.poll() is not None:
            stdout, stderr = client_process.communicate()
            print(f"❌ 客户端进程异常退出:")
            print(f"stdout: {stdout}")
            print(f"stderr: {stderr}")
            return False
        
        print("\n" + "=" * 50)
        print("🎮 双人联机测试环境已启动！")
        print("=" * 50)
        print()
        print("📋 测试指南:")
        print("1. 两个游戏窗口应该已经打开")
        print("2. 主机窗口显示绿色坦克（左侧）")
        print("3. 客户端窗口显示蓝色坦克（右侧）")
        print()
        print("🔧 修复验证项目:")
        print("✅ 主机端坦克控制（WASD + 空格）")
        print("🔍 客户端坦克控制（WASD + 空格）← 重点测试")
        print("🔍 客户端移动同步到主机端显示 ← 重点测试")
        print("🔍 客户端射击同步到主机端显示 ← 重点测试")
        print("✅ 双方都能看到对方的实时操作")
        print()
        print("⚠️ 测试说明:")
        print("- 在客户端窗口中使用WASD控制蓝色坦克移动")
        print("- 在客户端窗口中按空格发射子弹")
        print("- 观察主机端窗口是否能看到客户端坦克的移动和射击")
        print("- 如果客户端坦克能正常移动和射击，说明修复成功")
        print()
        print("🛑 按 Ctrl+C 结束测试")
        
        # 等待用户测试
        try:
            while True:
                time.sleep(1)
                
                # 检查进程是否还在运行
                if host_process.poll() is not None:
                    print("\n⚠️ 主机进程已退出")
                    break
                
                if client_process.poll() is not None:
                    print("\n⚠️ 客户端进程已退出")
                    break
                    
        except KeyboardInterrupt:
            print("\n\n🛑 用户中断测试")
        
        # 终止进程
        print("\n🧹 清理测试环境...")
        
        try:
            host_process.terminate()
            host_process.wait(timeout=5)
        except:
            try:
                host_process.kill()
            except:
                pass
        
        try:
            client_process.terminate()
            client_process.wait(timeout=5)
        except:
            try:
                client_process.kill()
            except:
                pass
        
        print("✅ 测试环境已清理")
        
        print("\n" + "=" * 50)
        print("📝 修复验证总结:")
        print("1. 如果客户端坦克能够响应WASD键移动 → 移动控制修复成功")
        print("2. 如果客户端坦克能够响应空格键射击 → 射击控制修复成功")
        print("3. 如果主机端能看到客户端的操作 → 网络同步修复成功")
        print("4. 如果双方都能实时看到对方操作 → 双向同步正常")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        cleanup_temp_files()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
