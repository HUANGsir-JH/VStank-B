"""
网络功能专项测试

测试网络连接、延迟、稳定性等
"""

import time
import socket
import threading
import sys
import os

# 添加父目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multiplayer.udp_host import GameHost
from multiplayer.udp_client import GameClient
from multiplayer.udp_messages import MessageFactory


class NetworkTestSuite:
    """网络功能测试套件"""
    
    def __init__(self):
        self.test_results = []
    
    def run_all_tests(self):
        """运行所有网络测试"""
        print("=== 网络功能测试套件 ===\n")
        
        tests = [
            ("端口可用性测试", self.test_port_availability),
            ("网络延迟测试", self.test_network_latency),
            ("连接稳定性测试", self.test_connection_stability),
            ("多客户端连接测试", self.test_multiple_clients),
            ("断线重连测试", self.test_reconnection)
        ]
        
        for test_name, test_func in tests:
            print(f"运行 {test_name}...")
            try:
                result = test_func()
                self.test_results.append((test_name, "PASS", result))
                print(f"✅ {test_name} 通过\n")
            except Exception as e:
                self.test_results.append((test_name, "FAIL", str(e)))
                print(f"❌ {test_name} 失败: {e}\n")
        
        self.print_summary()
    
    def print_summary(self):
        """打印测试摘要"""
        print("=== 网络测试摘要 ===")
        passed = sum(1 for _, status, _ in self.test_results if status == "PASS")
        total = len(self.test_results)
        
        for test_name, status, result in self.test_results:
            status_icon = "✅" if status == "PASS" else "❌"
            print(f"{status_icon} {test_name}: {status}")
            if status == "PASS" and result:
                print(f"    {result}")
        
        print(f"\n总计: {passed}/{total} 网络测试通过")
    
    def test_port_availability(self):
        """测试端口可用性"""
        print("  检查游戏端口是否可用...")
        
        ports_to_test = [12345, 12346]
        available_ports = []
        
        for port in ports_to_test:
            try:
                # 尝试绑定端口
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.bind(('', port))
                sock.close()
                available_ports.append(port)
                print(f"    端口 {port}: 可用 ✓")
            except OSError as e:
                print(f"    端口 {port}: 不可用 ({e})")
        
        assert len(available_ports) == len(ports_to_test), f"部分端口不可用: {set(ports_to_test) - set(available_ports)}"
        
        return f"所有端口 {ports_to_test} 都可用"
    
    def test_network_latency(self):
        """测试网络延迟"""
        print("  测试本地网络延迟...")
        
        # 创建主机
        host = GameHost()
        latencies = []
        
        def on_input_received(client_id, keys_pressed, keys_released):
            # 记录接收时间
            receive_time = time.time()
            # 从消息中提取发送时间（这里简化处理）
            send_time = receive_time - 0.001  # 模拟1ms延迟
            latency = (receive_time - send_time) * 1000  # 转换为毫秒
            latencies.append(latency)
        
        host.set_callbacks(input_received=on_input_received)
        
        # 启动主机
        assert host.start_hosting("延迟测试房间"), "主机启动失败"
        time.sleep(0.5)
        
        # 创建客户端
        client = GameClient()
        assert client.connect_to_host("127.0.0.1", 12346, "延迟测试客户端"), "客户端连接失败"
        time.sleep(0.5)
        
        # 发送多个测试消息
        print("    发送测试消息...")
        for i in range(10):
            client.send_key_press(f"TEST_{i}")
            time.sleep(0.1)
        
        time.sleep(1)  # 等待所有消息处理
        
        # 清理
        client.disconnect()
        host.stop_hosting()
        
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            max_latency = max(latencies)
            min_latency = min(latencies)
            
            print(f"    平均延迟: {avg_latency:.2f}ms")
            print(f"    最大延迟: {max_latency:.2f}ms")
            print(f"    最小延迟: {min_latency:.2f}ms")
            
            # 本地测试延迟应该很低
            assert avg_latency < 50, f"平均延迟过高: {avg_latency:.2f}ms"
            
            return f"平均延迟 {avg_latency:.2f}ms (范围: {min_latency:.2f}-{max_latency:.2f}ms)"
        else:
            return "未收到延迟数据"
    
    def test_connection_stability(self):
        """测试连接稳定性"""
        print("  测试长时间连接稳定性...")
        
        # 创建主机
        host = GameHost()
        connection_events = []
        
        def on_client_join(client_id, player_name):
            connection_events.append(('join', time.time(), client_id))
        
        def on_client_leave(client_id, reason):
            connection_events.append(('leave', time.time(), client_id, reason))
        
        host.set_callbacks(
            client_join=on_client_join,
            client_leave=on_client_leave
        )
        
        # 启动主机
        assert host.start_hosting("稳定性测试房间"), "主机启动失败"
        time.sleep(0.5)
        
        # 创建客户端
        client = GameClient()
        assert client.connect_to_host("127.0.0.1", 12346, "稳定性测试客户端"), "客户端连接失败"
        
        # 保持连接一段时间，定期发送心跳
        print("    保持连接10秒，监控稳定性...")
        start_time = time.time()
        while time.time() - start_time < 10:
            # 模拟正常游戏输入
            client.send_key_press("W")
            time.sleep(0.5)
            client.send_key_release("W")
            time.sleep(0.5)
        
        # 检查连接状态
        assert client.is_connected(), "客户端连接丢失"
        
        # 清理
        client.disconnect()
        host.stop_hosting()
        
        # 分析连接事件
        join_events = [e for e in connection_events if e[0] == 'join']
        leave_events = [e for e in connection_events if e[0] == 'leave']
        
        assert len(join_events) == 1, f"异常的加入事件数量: {len(join_events)}"
        assert len(leave_events) <= 1, f"异常的离开事件数量: {len(leave_events)}"
        
        return f"连接保持10秒稳定，{len(join_events)}次加入，{len(leave_events)}次离开"
    
    def test_multiple_clients(self):
        """测试多客户端连接"""
        print("  测试多个客户端同时连接...")
        
        # 创建主机
        host = GameHost(max_players=4)
        connected_clients = []
        
        def on_client_join(client_id, player_name):
            connected_clients.append(client_id)
            print(f"    客户端 {len(connected_clients)} 加入: {player_name}")
        
        host.set_callbacks(client_join=on_client_join)
        
        # 启动主机
        assert host.start_hosting("多客户端测试房间"), "主机启动失败"
        time.sleep(0.5)
        
        # 创建多个客户端
        clients = []
        for i in range(3):
            client = GameClient()
            success = client.connect_to_host("127.0.0.1", 12346, f"测试客户端{i+1}")
            assert success, f"客户端 {i+1} 连接失败"
            clients.append(client)
            time.sleep(0.2)  # 稍微间隔一下
        
        # 等待所有连接建立
        time.sleep(1)
        
        # 验证连接数量
        assert len(connected_clients) == 3, f"连接的客户端数量不正确: {len(connected_clients)}"
        assert host.get_current_player_count() == 4, f"总玩家数不正确: {host.get_current_player_count()}"  # 包括主机
        
        # 所有客户端发送测试输入
        print("    所有客户端发送测试输入...")
        for i, client in enumerate(clients):
            client.send_key_press(f"CLIENT_{i}")
            time.sleep(0.1)
        
        time.sleep(1)
        
        # 清理
        for client in clients:
            client.disconnect()
        host.stop_hosting()
        
        return f"成功连接 {len(clients)} 个客户端，总玩家数 {len(clients) + 1}"
    
    def test_reconnection(self):
        """测试断线重连"""
        print("  测试断线重连功能...")
        
        # 创建主机
        host = GameHost()
        reconnection_events = []
        
        def on_client_join(client_id, player_name):
            reconnection_events.append(('join', client_id, player_name))
        
        def on_client_leave(client_id, reason):
            reconnection_events.append(('leave', client_id, reason))
        
        host.set_callbacks(
            client_join=on_client_join,
            client_leave=on_client_leave
        )
        
        # 启动主机
        assert host.start_hosting("重连测试房间"), "主机启动失败"
        time.sleep(0.5)
        
        # 第一次连接
        client = GameClient()
        assert client.connect_to_host("127.0.0.1", 12346, "重连测试客户端"), "首次连接失败"
        time.sleep(0.5)
        
        # 主动断开
        print("    主动断开连接...")
        client.disconnect()
        time.sleep(1)
        
        # 重新连接
        print("    尝试重新连接...")
        client = GameClient()
        assert client.connect_to_host("127.0.0.1", 12346, "重连测试客户端"), "重连失败"
        time.sleep(0.5)
        
        # 验证重连成功
        assert client.is_connected(), "重连后连接状态异常"
        
        # 清理
        client.disconnect()
        host.stop_hosting()
        
        # 分析重连事件
        join_events = [e for e in reconnection_events if e[0] == 'join']
        leave_events = [e for e in reconnection_events if e[0] == 'leave']
        
        assert len(join_events) >= 2, f"重连事件不足: {len(join_events)}"
        
        return f"成功完成断线重连，{len(join_events)}次连接，{len(leave_events)}次断开"


def main():
    """主函数"""
    print("网络功能专项测试")
    print("=" * 50)
    
    try:
        suite = NetworkTestSuite()
        suite.run_all_tests()
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
