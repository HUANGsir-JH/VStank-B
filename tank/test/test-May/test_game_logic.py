"""
游戏逻辑测试

测试坦克、子弹、物理引擎等游戏核心逻辑
"""

import sys
import os
import math

# 添加父目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tank_sprites import Tank, Bullet, COLLISION_TYPE_TANK, COLLISION_TYPE_BULLET
from maps import get_random_map_layout, get_map_constants


class GameLogicTestSuite:
    """游戏逻辑测试套件"""

    def __init__(self):
        self.test_results = []

    def run_all_tests(self):
        """运行所有游戏逻辑测试"""
        print("=== 游戏逻辑测试套件 ===\n")

        tests = [
            ("坦克创建测试", self.test_tank_creation),
            ("坦克移动测试", self.test_tank_movement),
            ("子弹发射测试", self.test_bullet_shooting),
            ("伤害系统测试", self.test_damage_system),
            ("地图生成测试", self.test_map_generation),
            ("物理引擎测试", self.test_physics_engine)
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
        print("=== 游戏逻辑测试摘要 ===")
        passed = sum(1 for _, status, _ in self.test_results if status == "PASS")
        total = len(self.test_results)

        for test_name, status, result in self.test_results:
            status_icon = "✅" if status == "PASS" else "❌"
            print(f"{status_icon} {test_name}: {status}")
            if status == "PASS" and result:
                print(f"    {result}")

        print(f"\n总计: {passed}/{total} 游戏逻辑测试通过")

    def test_tank_creation(self):
        """测试坦克创建"""
        print("  测试坦克对象创建...")

        # 测试不同参数的坦克创建
        test_cases = [
            (None, 0.5, 100, 200),  # 无图片
            ("nonexistent.png", 0.8, 300, 400),  # 不存在的图片
        ]

        created_tanks = []

        for i, (image_file, scale, x, y) in enumerate(test_cases):
            tank = Tank(image_file, scale, x, y)

            # 验证基本属性
            assert tank.center_x == x, f"坦克 {i+1} X坐标不正确"
            assert tank.center_y == y, f"坦克 {i+1} Y坐标不正确"
            assert tank.health == tank.max_health, f"坦克 {i+1} 初始血量不正确"
            assert tank.is_alive(), f"坦克 {i+1} 初始状态应该是活着的"

            # 验证物理属性
            assert tank.pymunk_body is not None, f"坦克 {i+1} 缺少物理体"
            assert tank.pymunk_shape is not None, f"坦克 {i+1} 缺少物理形状"
            assert tank.pymunk_shape.collision_type == COLLISION_TYPE_TANK, f"坦克 {i+1} 碰撞类型不正确"

            created_tanks.append(tank)
            print(f"    坦克 {i+1}: 创建成功 ✓")

        return f"成功创建 {len(created_tanks)} 个坦克"

    def test_tank_movement(self):
        """测试坦克移动"""
        print("  测试坦克移动和同步...")

        tank = Tank(None, 0.5, 100, 100)

        # 记录初始位置
        initial_x = tank.center_x
        initial_y = tank.center_y
        initial_angle = tank.angle

        # 测试位置移动
        new_x, new_y = 200, 250
        tank.pymunk_body.position = new_x, new_y
        tank.sync_with_pymunk_body()

        assert abs(tank.center_x - new_x) < 0.1, f"X坐标同步失败: {tank.center_x} != {new_x}"
        assert abs(tank.center_y - new_y) < 0.1, f"Y坐标同步失败: {tank.center_y} != {new_y}"
        print("    位置同步: 成功 ✓")

        # 测试角度旋转
        new_angle_rad = math.radians(45)
        tank.pymunk_body.angle = new_angle_rad
        tank.sync_with_pymunk_body()

        expected_arcade_angle = 90 - math.degrees(new_angle_rad)
        assert abs(tank.angle - expected_arcade_angle) < 0.1, f"角度同步失败: {tank.angle} != {expected_arcade_angle}"
        print("    角度同步: 成功 ✓")

        return f"移动测试完成，位置 ({tank.center_x:.1f}, {tank.center_y:.1f})，角度 {tank.angle:.1f}°"

    def test_bullet_shooting(self):
        """测试子弹发射"""
        print("  测试子弹发射系统...")

        tank = Tank(None, 0.5, 100, 100)
        tank.player_id = "test_player"

        # 测试射击冷却
        current_time = 0.0

        # 第一次射击应该成功
        bullet1 = tank.shoot(current_time)
        if bullet1 is None:
            print(f"    调试信息: 当前时间={current_time}, 上次射击时间={tank.last_shot_time}, 冷却时间={tank.shot_cooldown}")
        assert bullet1 is not None, "第一次射击失败"
        assert bullet1.owner is tank, "子弹所有者不正确"
        assert bullet1.pymunk_body is not None, "子弹缺少物理体"
        assert bullet1.pymunk_shape.collision_type == COLLISION_TYPE_BULLET, "子弹碰撞类型不正确"
        print("    第一次射击: 成功 ✓")

        # 立即再次射击应该失败（冷却时间）
        bullet2 = tank.shoot(current_time)
        assert bullet2 is None, "射击冷却时间未生效"
        print("    射击冷却: 生效 ✓")

        # 等待冷却时间后再次射击
        current_time += tank.shot_cooldown + 0.1
        bullet3 = tank.shoot(current_time)
        assert bullet3 is not None, "冷却后射击失败"
        print("    冷却后射击: 成功 ✓")

        # 验证子弹属性
        assert bullet3.bounce_count == 0, "子弹初始反弹次数不正确"
        assert bullet3.max_bounces > 0, "子弹最大反弹次数不正确"

        return f"射击测试完成，冷却时间 {tank.shot_cooldown}s"

    def test_damage_system(self):
        """测试伤害系统"""
        print("  测试坦克伤害和生命系统...")

        tank = Tank(None, 0.5, 100, 100)
        initial_health = tank.health
        max_health = tank.max_health

        assert tank.is_alive(), "坦克初始状态应该是活着的"
        print(f"    初始血量: {initial_health}/{max_health} ✓")

        # 测试受到伤害
        damage_amount = 2
        tank.take_damage(damage_amount)

        expected_health = initial_health - damage_amount
        assert tank.health == expected_health, f"伤害计算错误: {tank.health} != {expected_health}"
        assert tank.is_alive(), "坦克受伤后应该还活着"
        print(f"    受到伤害: {tank.health}/{max_health} ✓")

        # 测试致命伤害
        fatal_damage = tank.health + 10
        tank.take_damage(fatal_damage)

        assert tank.health == 0, f"致命伤害后血量应该为0: {tank.health}"
        assert not tank.is_alive(), "坦克应该已经死亡"
        print("    致命伤害: 坦克死亡 ✓")

        # 测试过量伤害不会导致负血量
        tank.take_damage(5)
        assert tank.health == 0, f"死亡后血量不应该为负: {tank.health}"

        return f"伤害系统测试完成，最终血量 {tank.health}/{max_health}"

    def test_map_generation(self):
        """测试地图生成"""
        print("  测试地图生成系统...")

        # 测试多次地图生成
        generated_maps = []
        for i in range(5):
            map_layout = get_random_map_layout()
            assert isinstance(map_layout, list), f"地图 {i+1} 格式不正确"
            assert len(map_layout) > 0, f"地图 {i+1} 为空"

            # 验证地图元素格式
            for j, wall in enumerate(map_layout):
                assert len(wall) == 4, f"地图 {i+1} 墙壁 {j+1} 格式不正确: {wall}"
                cx, cy, w, h = wall
                assert isinstance(cx, (int, float)), f"地图 {i+1} 墙壁 {j+1} X坐标类型错误"
                assert isinstance(cy, (int, float)), f"地图 {i+1} 墙壁 {j+1} Y坐标类型错误"
                assert w > 0, f"地图 {i+1} 墙壁 {j+1} 宽度无效"
                assert h > 0, f"地图 {i+1} 墙壁 {j+1} 高度无效"

            generated_maps.append(map_layout)
            print(f"    地图 {i+1}: {len(map_layout)} 个墙壁 ✓")

        # 测试地图常量
        constants = get_map_constants()
        required_keys = ["map_min_x", "map_max_x", "game_area_bottom_y", "game_area_top_y"]
        for key in required_keys:
            assert key in constants, f"缺少地图常量: {key}"
            assert isinstance(constants[key], (int, float)), f"地图常量 {key} 类型错误"

        print("    地图常量: 验证通过 ✓")

        return f"生成 {len(generated_maps)} 个地图，平均 {sum(len(m) for m in generated_maps) / len(generated_maps):.1f} 个墙壁"

    def test_physics_engine(self):
        """测试物理引擎集成"""
        print("  测试物理引擎集成...")

        import pymunk

        # 创建物理空间
        space = pymunk.Space()
        space.gravity = (0, 0)

        # 创建坦克并添加到物理空间
        tank = Tank(None, 0.5, 100, 100)
        space.add(tank.pymunk_body, tank.pymunk_shape)

        # 验证物理体属性
        assert tank.pymunk_body.mass > 0, "坦克质量应该大于0"
        assert tank.pymunk_body.moment > 0, "坦克转动惯量应该大于0"
        print("    坦克物理属性: 验证通过 ✓")

        # 创建子弹并添加到物理空间
        bullet = tank.shoot(0.0)
        if bullet:
            space.add(bullet.pymunk_body, bullet.pymunk_shape)

            # 验证子弹物理属性
            assert bullet.pymunk_body.mass > 0, "子弹质量应该大于0"
            assert bullet.pymunk_shape.radius > 0, "子弹半径应该大于0"
            print("    子弹物理属性: 验证通过 ✓")

            # 测试物理模拟
            initial_pos = bullet.pymunk_body.position
            space.step(1/60.0)  # 模拟一帧

            # 子弹应该有移动（因为有初始速度）
            new_pos = bullet.pymunk_body.position
            distance_moved = ((new_pos.x - initial_pos.x)**2 + (new_pos.y - initial_pos.y)**2)**0.5
            assert distance_moved > 0, "子弹在物理模拟中没有移动"
            print(f"    物理模拟: 子弹移动 {distance_moved:.2f} 像素 ✓")

        # 清理物理空间
        for body in space.bodies:
            space.remove(body)
        for shape in space.shapes:
            space.remove(shape)

        return "物理引擎集成测试完成"


def main():
    """主函数"""
    print("游戏逻辑测试")
    print("=" * 50)

    try:
        suite = GameLogicTestSuite()
        suite.run_all_tests()
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
