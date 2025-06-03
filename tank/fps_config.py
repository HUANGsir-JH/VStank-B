"""
FPS配置管理模块

统一管理游戏的帧率设置，确保主机端和客户端的刷新率同步。
"""

import arcade
import time
from typing import Optional, Dict, Any


class FPSConfig:
    """FPS配置类 - 统一管理游戏帧率设置"""
    
    # 预定义的FPS配置方案
    PRESETS = {
        "high_performance": {
            "target_fps": 60,
            "network_sync_fps": 60,
            "physics_fps": 60,
            "description": "高性能模式 - 最佳游戏体验"
        },
        "balanced": {
            "target_fps": 60,
            "network_sync_fps": 45,
            "physics_fps": 60,
            "description": "平衡模式 - 性能与流畅度兼顾"
        },
        "power_saving": {
            "target_fps": 45,
            "network_sync_fps": 30,
            "physics_fps": 45,
            "description": "节能模式 - 适合低配置设备"
        }
    }
    
    def __init__(self, preset: str = "high_performance"):
        """
        初始化FPS配置
        
        Args:
            preset: 预设配置名称
        """
        if preset not in self.PRESETS:
            preset = "high_performance"
            
        config = self.PRESETS[preset]
        self.target_fps = config["target_fps"]
        self.network_sync_fps = config["network_sync_fps"]
        self.physics_fps = config["physics_fps"]
        self.preset_name = preset
        
        # 计算相关间隔
        self.frame_interval = 1.0 / self.target_fps
        self.network_interval = 1.0 / self.network_sync_fps
        self.physics_interval = 1.0 / self.physics_fps
        
        # 性能监控
        self.actual_fps = 0.0
        self.frame_count = 0
        self.last_fps_update = time.time()
        self.fps_history = []
        
        print(f"🎯 FPS配置已设置: {config['description']}")
        print(f"   目标FPS: {self.target_fps}")
        print(f"   网络同步FPS: {self.network_sync_fps}")
        print(f"   物理更新FPS: {self.physics_fps}")
    
    def apply_to_window(self, window: arcade.Window):
        """将FPS设置应用到窗口"""
        window.set_update_rate(self.frame_interval)
        print(f"✅ 窗口FPS已设置为: {self.target_fps}")
    
    def should_sync_network(self, current_time: float, last_sync_time: float) -> bool:
        """检查是否应该进行网络同步"""
        return (current_time - last_sync_time) >= self.network_interval
    
    def get_physics_delta_limit(self) -> float:
        """获取物理更新的最大时间步长"""
        return self.physics_interval
    
    def update_fps_counter(self):
        """更新FPS计数器"""
        self.frame_count += 1
        current_time = time.time()
        
        # 每秒更新一次FPS统计
        if current_time - self.last_fps_update >= 1.0:
            self.actual_fps = self.frame_count / (current_time - self.last_fps_update)
            self.fps_history.append(self.actual_fps)
            
            # 保持历史记录在合理范围内
            if len(self.fps_history) > 60:
                self.fps_history.pop(0)
                
            self.frame_count = 0
            self.last_fps_update = current_time
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        avg_fps = sum(self.fps_history) / len(self.fps_history) if self.fps_history else 0.0
        
        # 计算FPS稳定性
        if len(self.fps_history) >= 5:
            recent_fps = self.fps_history[-5:]
            avg_recent = sum(recent_fps) / len(recent_fps)
            variance = sum((fps - avg_recent) ** 2 for fps in recent_fps) / len(recent_fps)
            stability = "稳定" if variance < 25 else "不稳定"
        else:
            stability = "数据不足"
        
        return {
            "preset": self.preset_name,
            "target_fps": self.target_fps,
            "actual_fps": self.actual_fps,
            "average_fps": avg_fps,
            "stability": stability,
            "network_sync_fps": self.network_sync_fps,
            "physics_fps": self.physics_fps
        }
    
    def create_fps_display_text(self) -> arcade.Text:
        """创建FPS显示文本对象"""
        return arcade.Text(
            "FPS: --",
            x=10,
            y=10,
            color=arcade.color.WHITE,
            font_size=14,
            font_name="Arial"
        )
    
    def update_fps_display(self, fps_text: arcade.Text):
        """更新FPS显示文本"""
        self.update_fps_counter()
        stats = self.get_performance_stats()
        
        fps_text.text = (
            f"FPS: {stats['actual_fps']:.1f}/{stats['target_fps']} "
            f"(平均: {stats['average_fps']:.1f}) [{stats['stability']}]"
        )


class NetworkSyncOptimizer:
    """网络同步优化器"""
    
    def __init__(self, fps_config: FPSConfig):
        self.fps_config = fps_config
        self.last_sync_time = 0.0
        self.sync_count = 0
        self.dropped_syncs = 0
        self.bandwidth_monitor = BandwidthMonitor()
    
    def should_sync(self, current_time: float) -> bool:
        """检查是否应该进行网络同步"""
        if self.fps_config.should_sync_network(current_time, self.last_sync_time):
            self.last_sync_time = current_time
            self.sync_count += 1
            return True
        return False
    
    def optimize_sync_data(self, game_state: dict) -> dict:
        """优化同步数据，减少网络负载"""
        # 只同步必要的数据
        optimized_state = {
            "tanks": [],
            "bullets": [],
            "round_info": game_state.get("round_info", {})
        }
        
        # 优化坦克数据
        for tank in game_state.get("tanks", []):
            optimized_tank = {
                "id": tank.get("id"),
                "x": round(tank.get("x", 0), 1),  # 减少精度
                "y": round(tank.get("y", 0), 1),
                "angle": round(tank.get("angle", 0), 1),
                "health": tank.get("health", 100),
                "alive": tank.get("alive", True)
            }
            optimized_state["tanks"].append(optimized_tank)
        
        # 优化子弹数据
        for bullet in game_state.get("bullets", []):
            optimized_bullet = {
                "id": bullet.get("id"),
                "x": round(bullet.get("x", 0), 1),
                "y": round(bullet.get("y", 0), 1),
                "angle": round(bullet.get("angle", 0), 1),
                "owner": bullet.get("owner")
            }
            optimized_state["bullets"].append(optimized_bullet)
        
        # 记录带宽使用
        self.bandwidth_monitor.record_sync(optimized_state)
        
        return optimized_state
    
    def get_sync_stats(self) -> dict:
        """获取同步统计信息"""
        return {
            "sync_fps": self.fps_config.network_sync_fps,
            "sync_count": self.sync_count,
            "dropped_syncs": self.dropped_syncs,
            "bandwidth_stats": self.bandwidth_monitor.get_stats()
        }


class BandwidthMonitor:
    """带宽监控器"""
    
    def __init__(self):
        self.data_sent = 0
        self.sync_count = 0
        self.start_time = time.time()
    
    def record_sync(self, data: dict):
        """记录同步数据"""
        # 估算数据大小（简化计算）
        data_size = len(str(data).encode('utf-8'))
        self.data_sent += data_size
        self.sync_count += 1
    
    def get_stats(self) -> dict:
        """获取带宽统计"""
        elapsed_time = time.time() - self.start_time
        if elapsed_time > 0:
            avg_bandwidth = self.data_sent / elapsed_time  # 字节/秒
            avg_sync_size = self.data_sent / max(self.sync_count, 1)
        else:
            avg_bandwidth = 0
            avg_sync_size = 0
        
        return {
            "total_data_sent": self.data_sent,
            "avg_bandwidth_bps": avg_bandwidth,
            "avg_sync_size_bytes": avg_sync_size,
            "sync_count": self.sync_count
        }


# 全局FPS配置实例
_global_fps_config: Optional[FPSConfig] = None


def get_fps_config() -> FPSConfig:
    """获取全局FPS配置"""
    global _global_fps_config
    if _global_fps_config is None:
        _global_fps_config = FPSConfig("high_performance")
    return _global_fps_config


def set_fps_config(preset: str = "high_performance") -> FPSConfig:
    """设置全局FPS配置"""
    global _global_fps_config
    _global_fps_config = FPSConfig(preset)
    return _global_fps_config


def apply_fps_to_window(window: arcade.Window):
    """将FPS配置应用到窗口"""
    fps_config = get_fps_config()
    fps_config.apply_to_window(window)
