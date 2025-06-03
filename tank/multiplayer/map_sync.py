"""
地图同步工具模块
处理地图数据的序列化、反序列化和校验
"""

import hashlib
import json
from typing import List, Tuple, Dict, Any, Optional


class MapSyncManager:
    """地图同步管理器"""
    
    @staticmethod
    def calculate_map_checksum(map_layout: List[Tuple[float, float, float, float]]) -> str:
        """计算地图布局的校验和"""
        # 将地图数据转换为字符串并计算MD5
        map_str = json.dumps(map_layout, sort_keys=True)
        return hashlib.md5(map_str.encode('utf-8')).hexdigest()
    
    @staticmethod
    def validate_map_layout(map_layout: List[Tuple[float, float, float, float]]) -> bool:
        """验证地图布局数据的有效性"""
        if not isinstance(map_layout, list):
            return False
        
        if len(map_layout) == 0:
            return False
        
        for wall in map_layout:
            if not isinstance(wall, (list, tuple)) or len(wall) != 4:
                return False
            
            cx, cy, w, h = wall
            if not all(isinstance(val, (int, float)) for val in [cx, cy, w, h]):
                return False
            
            if w <= 0 or h <= 0:
                return False
        
        return True
    
    @staticmethod
    def serialize_map_data(map_layout: List[Tuple[float, float, float, float]]) -> Dict[str, Any]:
        """序列化地图数据"""
        if not MapSyncManager.validate_map_layout(map_layout):
            raise ValueError("无效的地图布局数据")
        
        checksum = MapSyncManager.calculate_map_checksum(map_layout)
        
        return {
            "map_layout": map_layout,
            "wall_count": len(map_layout),
            "checksum": checksum,
            "version": "1.0"
        }
    
    @staticmethod
    def deserialize_map_data(map_data: Dict[str, Any]) -> List[Tuple[float, float, float, float]]:
        """反序列化地图数据并验证完整性"""
        if not isinstance(map_data, dict):
            raise ValueError("地图数据格式错误")
        
        required_fields = ["map_layout", "wall_count", "checksum"]
        for field in required_fields:
            if field not in map_data:
                raise ValueError(f"缺少必需字段: {field}")
        
        map_layout = map_data["map_layout"]
        expected_count = map_data["wall_count"]
        expected_checksum = map_data["checksum"]
        
        # 验证地图布局
        if not MapSyncManager.validate_map_layout(map_layout):
            raise ValueError("地图布局数据无效")
        
        # 验证墙壁数量
        if len(map_layout) != expected_count:
            raise ValueError(f"墙壁数量不匹配: 期望 {expected_count}, 实际 {len(map_layout)}")
        
        # 验证校验和
        actual_checksum = MapSyncManager.calculate_map_checksum(map_layout)
        if actual_checksum != expected_checksum:
            raise ValueError(f"地图数据校验失败: 期望 {expected_checksum}, 实际 {actual_checksum}")
        
        return map_layout
    
    @staticmethod
    def compare_maps(map1: List[Tuple[float, float, float, float]], 
                    map2: List[Tuple[float, float, float, float]]) -> bool:
        """比较两个地图是否相同"""
        if len(map1) != len(map2):
            return False
        
        # 使用校验和比较
        checksum1 = MapSyncManager.calculate_map_checksum(map1)
        checksum2 = MapSyncManager.calculate_map_checksum(map2)
        
        return checksum1 == checksum2
    
    @staticmethod
    def get_map_info(map_layout: List[Tuple[float, float, float, float]]) -> Dict[str, Any]:
        """获取地图信息摘要"""
        if not MapSyncManager.validate_map_layout(map_layout):
            return {"valid": False, "error": "无效的地图布局"}
        
        # 计算地图边界
        min_x = min(wall[0] - wall[2]/2 for wall in map_layout)
        max_x = max(wall[0] + wall[2]/2 for wall in map_layout)
        min_y = min(wall[1] - wall[3]/2 for wall in map_layout)
        max_y = max(wall[1] + wall[3]/2 for wall in map_layout)
        
        # 计算总面积
        total_area = sum(wall[2] * wall[3] for wall in map_layout)
        
        return {
            "valid": True,
            "wall_count": len(map_layout),
            "bounds": {
                "min_x": min_x,
                "max_x": max_x,
                "min_y": min_y,
                "max_y": max_y
            },
            "total_wall_area": total_area,
            "checksum": MapSyncManager.calculate_map_checksum(map_layout)
        }


def test_map_sync_manager():
    """测试地图同步管理器"""
    print("🧪 测试地图同步管理器...")
    
    # 测试地图数据
    test_map = [
        (100, 200, 50, 30),  # cx, cy, w, h
        (300, 400, 80, 40),
        (500, 300, 60, 60)
    ]
    
    # 测试序列化
    serialized = MapSyncManager.serialize_map_data(test_map)
    print(f"  序列化数据: {serialized}")
    
    # 测试反序列化
    deserialized = MapSyncManager.deserialize_map_data(serialized)
    print(f"  反序列化成功: {len(deserialized)} 个墙壁")
    
    # 测试比较
    is_same = MapSyncManager.compare_maps(test_map, deserialized)
    print(f"  地图比较结果: {is_same}")
    
    # 测试地图信息
    map_info = MapSyncManager.get_map_info(test_map)
    print(f"  地图信息: {map_info}")
    
    print("✅ 地图同步管理器测试完成")


if __name__ == "__main__":
    test_map_sync_manager()
