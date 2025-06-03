"""
网络游戏视图模块 - 重构版

专为1对1双人游戏设计的网络视图层
"""

import arcade
from typing import List, Dict, Any
from .game_host import GameHost
from .game_client import GameClient
from .room_discovery import RoomDiscovery, RoomInfo
from .messages import MessageFactory


# 文本绘制优化说明：
# 为了提高性能，我们在每个视图类中预创建静态Text对象，
# 避免在每次绘制时重新创建文本对象


class RoomBrowserView(arcade.View):
    """房间浏览视图 - 重构版"""

    def __init__(self):
        super().__init__()
        self.room_discovery = RoomDiscovery()
        self.discovered_rooms: List[RoomInfo] = []
        self.selected_room_index = 0
        self.player_name = "玩家"

        # UI状态
        self.refresh_timer = 0
        self.refresh_interval = 1.0  # 每秒刷新一次

        # 防止重复初始化的标志
        self.discovery_started = False

        # 预创建静态文本对象以提高性能
        self.title_text = arcade.Text(
            "房间浏览器",
            x=0, y=0,
            color=arcade.color.WHITE,
            font_size=30,
            anchor_x="center"
        )

        self.help_text = arcade.Text(
            "按 H 创建房间 | 按 ESC 返回主菜单",
            x=0, y=0,
            color=arcade.color.LIGHT_GRAY,
            font_size=16,
            anchor_x="center"
        )

        self.instruction_text = arcade.Text(
            "按 ENTER 加入选中房间 | 上下箭头选择房间",
            x=0, y=0,
            color=arcade.color.YELLOW,
            font_size=14,
            anchor_x="center"
        )

        self.no_rooms_text = arcade.Text(
            "未发现房间，正在搜索...",
            x=0, y=0,
            color=arcade.color.LIGHT_GRAY,
            font_size=20,
            anchor_x="center"
        )
    
    def on_show_view(self):
        """显示视图时的初始化"""
        arcade.set_background_color(arcade.color.DARK_BLUE_GRAY)

        # 防止重复启动房间发现
        if not self.discovery_started:
            self.discovery_started = True
            self.room_discovery.start_discovery(self._on_rooms_updated)
            print("开始搜索房间...")
        else:
            print("房间搜索已在运行中，跳过重复启动")
    
    def on_hide_view(self):
        """隐藏视图时的清理"""
        self.room_discovery.stop_discovery()
        # 重置标志，允许下次重新启动
        self.discovery_started = False
    
    def on_draw(self):
        """绘制界面"""
        self.clear()

        # 使用预创建的Text对象绘制标题
        self.title_text.x = self.window.width // 2
        self.title_text.y = self.window.height - 50
        self.title_text.draw()

        # 使用预创建的Text对象绘制说明文字
        self.help_text.x = self.window.width // 2
        self.help_text.y = self.window.height - 100
        self.help_text.draw()
        
        # 房间列表
        if self.discovered_rooms:
            y_start = self.window.height - 200
            for i, room in enumerate(self.discovered_rooms):
                y = y_start - i * 60
                
                # 选中高亮
                if i == self.selected_room_index:
                    # 使用正确的Arcade API函数
                    center_x = self.window.width // 2
                    center_y = y
                    width = 600
                    height = 50

                    # 计算矩形边界 (left, right, bottom, top)
                    left = center_x - width // 2
                    right = center_x + width // 2
                    bottom = center_y - height // 2
                    top = center_y + height // 2

                    arcade.draw_lrbt_rectangle_filled(
                        left, right, bottom, top,
                        arcade.color.BLUE_GRAY
                    )
                
                # 房间信息 - 使用临时Text对象
                room_text = f"{room.room_name} ({room.host_name})"
                room_text_obj = arcade.Text(
                    room_text,
                    x=self.window.width // 2 - 280,
                    y=y + 10,
                    color=arcade.color.WHITE,
                    font_size=16
                )
                room_text_obj.draw()

                # 玩家数量 - 使用临时Text对象
                player_text = f"{room.players}/{room.max_players}"
                player_text_obj = arcade.Text(
                    player_text,
                    x=self.window.width // 2 + 200,
                    y=y + 10,
                    color=arcade.color.LIGHT_GRAY,
                    font_size=16
                )
                player_text_obj.draw()

            # 使用预创建的Text对象绘制连接说明
            self.instruction_text.x = self.window.width // 2
            self.instruction_text.y = 100
            self.instruction_text.draw()
        else:
            # 使用预创建的Text对象绘制无房间提示
            self.no_rooms_text.x = self.window.width // 2
            self.no_rooms_text.y = self.window.height // 2
            self.no_rooms_text.draw()
    
    def on_update(self, delta_time):
        """更新逻辑"""
        self.refresh_timer += delta_time
        if self.refresh_timer >= self.refresh_interval:
            self.refresh_timer = 0
            self.discovered_rooms = self.room_discovery.get_discovered_rooms()
            
            # 调整选中索引
            if self.selected_room_index >= len(self.discovered_rooms):
                self.selected_room_index = max(0, len(self.discovered_rooms) - 1)
    
    def on_key_press(self, key, _modifiers):
        """处理按键事件"""
        if key == arcade.key.ESCAPE:
            # 返回主菜单
            import game_views
            mode_view = game_views.ModeSelectView()
            self.window.show_view(mode_view)

        elif key == arcade.key.H:
            # 创建房间
            host_view = HostGameView()
            self.window.show_view(host_view)

        elif key == arcade.key.ENTER and self.discovered_rooms:
            # 加入选中房间
            selected_room = self.discovered_rooms[self.selected_room_index]
            client_view = ClientGameView()
            success = client_view.connect_to_room(
                selected_room.host_ip,
                selected_room.host_port,
                self.player_name
            )
            if success:
                self.window.show_view(client_view)
            else:
                print("连接房间失败")

        elif key == arcade.key.UP and self.discovered_rooms:
            # 向上选择
            self.selected_room_index = max(0, self.selected_room_index - 1)

        elif key == arcade.key.DOWN and self.discovered_rooms:
            # 向下选择
            self.selected_room_index = min(
                len(self.discovered_rooms) - 1,
                self.selected_room_index + 1
            )
    
    def _on_rooms_updated(self, rooms: List[RoomInfo]):
        """房间列表更新回调"""
        self.discovered_rooms = rooms


class HostGameView(arcade.View):
    """主机游戏视图 - 重构版"""

    def __init__(self):
        super().__init__()
        self.game_host = GameHost()
        self.room_name = "我的房间"
        self.host_name = "主机"

        # 游戏状态
        self.game_phase = "waiting"  # waiting -> playing
        self.connected_players = ["主机"]
        self.game_view = None

        # 坦克选择信息
        self.tank_selections = {}

        # 预创建静态文本对象
        self.waiting_text = arcade.Text(
            "等待玩家加入...",
            x=0, y=0,
            color=arcade.color.WHITE,
            font_size=30,
            anchor_x="center"
        )

        self.start_game_text = arcade.Text(
            "按 SPACE 开始游戏",
            x=0, y=0,
            color=arcade.color.YELLOW,
            font_size=20,
            anchor_x="center"
        )

        self.back_text = arcade.Text(
            "按 ESC 返回房间浏览",
            x=0, y=0,
            color=arcade.color.LIGHT_GRAY,
            font_size=14,
            anchor_x="center"
        )
    
    def on_show_view(self):
        """显示视图时的初始化"""
        arcade.set_background_color(arcade.color.DARK_GREEN)
        
        # 设置回调
        self.game_host.set_callbacks(
            client_join=self._on_client_join,
            client_leave=self._on_client_leave,
            input_received=self._on_input_received
        )
        
        # 启动主机
        success = self.game_host.start_hosting(self.room_name, self.host_name)
        if not success:
            print("启动主机失败")
            # 返回房间浏览
            browser_view = RoomBrowserView()
            self.window.show_view(browser_view)
    
    def on_hide_view(self):
        """隐藏视图时的清理"""
        self.game_host.stop_hosting()
    
    def on_draw(self):
        """绘制界面"""
        self.clear()

        if self.game_phase == "waiting":
            # 使用预创建的Text对象绘制等待界面
            self.waiting_text.x = self.window.width // 2
            self.waiting_text.y = self.window.height // 2 + 50
            self.waiting_text.draw()

            # 显示连接的玩家
            y_start = self.window.height // 2
            for i, player in enumerate(self.connected_players):
                player_text = arcade.Text(
                    f"玩家 {i+1}: {player}",
                    x=self.window.width // 2,
                    y=y_start - i * 30,
                    color=arcade.color.LIGHT_GRAY,
                    font_size=16,
                    anchor_x="center"
                )
                player_text.draw()

            # 说明文字
            if len(self.connected_players) >= 2:
                self.start_game_text.x = self.window.width // 2
                self.start_game_text.y = 150
                self.start_game_text.draw()

            self.back_text.x = self.window.width // 2
            self.back_text.y = 100
            self.back_text.draw()

        elif self.game_phase == "playing" and self.game_view:
            # 游戏进行中，委托给游戏视图
            self.game_view.on_draw()
    
    def on_update(self, delta_time):
        """更新逻辑"""
        if self.game_phase == "playing" and self.game_view:
            self.game_view.on_update(delta_time)

            # 降低游戏状态同步频率，避免子弹状态被过于频繁地清除重建
            # 使用计时器控制同步频率
            if not hasattr(self, '_last_sync_time'):
                self._last_sync_time = 0

            current_time = getattr(self.game_view, 'total_time', 0)
            sync_interval = 1.0 / 30.0  # 30 FPS同步频率，而不是60 FPS

            if current_time - self._last_sync_time >= sync_interval:
                self._last_sync_time = current_time
                # 发送游戏状态给客户端
                game_state = self._get_game_state()
                self.game_host.send_game_state(game_state)
    
    def on_key_press(self, key, _modifiers):
        """处理按键事件"""
        if key == arcade.key.ESCAPE and self.game_phase == "waiting":
            # 返回房间浏览
            browser_view = RoomBrowserView()
            self.window.show_view(browser_view)

        elif key == arcade.key.SPACE and self.game_phase == "waiting":
            # 开始游戏
            if len(self.connected_players) >= 2:
                self._start_game()
            else:
                print("需要2个玩家才能开始游戏")

        elif self.game_phase == "playing" and self.game_view:
            # 转发给游戏视图
            self.game_view.on_key_press(key, _modifiers)

    def on_key_release(self, key, _modifiers):
        """处理按键释放事件"""
        if self.game_phase == "playing" and self.game_view:
            self.game_view.on_key_release(key, _modifiers)
    
    def _on_client_join(self, client_id: str, player_name: str):
        """客户端加入回调"""
        self.connected_players.append(f"{player_name} ({client_id})")
        print(f"玩家加入: {player_name}")
    
    def _on_client_leave(self, client_id: str, reason: str):
        """客户端离开回调"""
        # 移除玩家
        self.connected_players = [p for p in self.connected_players if client_id not in p]
        print(f"玩家离开: {client_id} ({reason})")
        
        # 如果游戏进行中，暂停游戏
        if self.game_phase == "playing":
            self.game_phase = "waiting"
            self.game_view = None
    
    def _on_input_received(self, client_id: str, keys_pressed: list, keys_released: list):
        """输入接收回调"""
        if self.game_phase == "playing" and self.game_view:
            # 将客户端输入应用到游戏中
            self._apply_client_input(client_id, keys_pressed, keys_released)
    
    def _start_game(self):
        """开始游戏"""
        import game_views
        from .map_sync import MapSyncManager

        # 创建游戏视图
        self.game_view = game_views.GameView(mode="network_host")

        # 重要：先获取地图布局，再调用setup
        map_layout = self.game_view.get_map_layout()

        # 验证地图数据
        if not MapSyncManager.validate_map_layout(map_layout):
            print("❌ 地图数据无效，使用默认地图")
            from maps import MAP_1_WALLS
            map_layout = MAP_1_WALLS
            self.game_view.set_map_layout(map_layout)

        # 序列化地图数据
        try:
            map_data = MapSyncManager.serialize_map_data(map_layout)
            print(f"✅ 地图数据已序列化: {map_data['wall_count']} 个墙壁, 校验和: {map_data['checksum'][:8]}...")
        except Exception as e:
            print(f"❌ 地图序列化失败: {e}")
            return

        # 调用setup方法初始化游戏元素
        self.game_view.setup()

        self.game_phase = "playing"

        print("游戏开始！")

        # 发送地图同步消息给客户端
        map_sync_msg = MessageFactory.create_map_sync(
            map_layout=map_layout,
            map_checksum=map_data['checksum']
        )
        self.game_host.send_to_client(map_sync_msg)

        # 通知客户端游戏开始
        start_msg = MessageFactory.create_game_start({
            "map_layout": map_layout,
            "map_checksum": map_data['checksum']
        })
        self.game_host.send_to_client(start_msg)

    def _get_game_state(self) -> Dict[str, Any]:
        """获取当前游戏状态"""
        if not self.game_view:
            return {}

        # 提取坦克状态
        tanks = []
        if hasattr(self.game_view, 'player_list') and self.game_view.player_list is not None:
            try:
                for tank in self.game_view.player_list:
                    if tank is not None:  # 确保坦克对象不为None
                        tanks.append({
                            "player_id": getattr(tank, 'player_id', 'unknown'),
                            "x": tank.center_x,
                            "y": tank.center_y,
                            "angle": tank.angle,
                            "health": getattr(tank, 'health', 5),
                            "tank_image_file": getattr(tank, 'tank_image_file', None)  # 添加坦克图片文件信息
                        })
            except Exception as e:
                print(f"获取坦克状态时出错: {e}")

        # 提取子弹状态
        bullets = []
        if hasattr(self.game_view, 'bullet_list') and self.game_view.bullet_list is not None:
            try:
                for bullet in self.game_view.bullet_list:
                    if bullet is not None:  # 确保子弹对象不为None
                        bullets.append({
                            "x": bullet.center_x,
                            "y": bullet.center_y,
                            "angle": getattr(bullet, 'angle', 0),
                            "owner": getattr(bullet.owner, 'player_id', 'unknown') if bullet.owner else 'unknown'
                        })
            except Exception as e:
                print(f"获取子弹状态时出错: {e}")

        # 提取分数和游戏状态
        scores = {}
        if hasattr(self.game_view, 'player1_score'):
            scores["host"] = self.game_view.player1_score
        if hasattr(self.game_view, 'player2_score'):
            scores["client"] = self.game_view.player2_score

        # 提取回合状态信息
        round_info = {}
        if hasattr(self.game_view, 'round_over'):
            round_info["round_over"] = self.game_view.round_over
        if hasattr(self.game_view, 'round_over_timer'):
            round_info["round_over_timer"] = self.game_view.round_over_timer
        if hasattr(self.game_view, 'round_result_text'):
            round_info["round_result_text"] = self.game_view.round_result_text

        return {
            "tanks": tanks,
            "bullets": bullets,
            "scores": scores,
            "round_info": round_info
        }

    def _apply_client_input(self, _client_id: str, keys_pressed: list, keys_released: list):
        """应用客户端输入到游戏中"""
        if not self.game_view or not hasattr(self.game_view, 'player2_tank'):
            return

        # 假设客户端控制player2_tank
        tank = self.game_view.player2_tank
        if not tank or not hasattr(tank, 'pymunk_body') or not tank.pymunk_body:
            return

        # 获取Pymunk body用于物理控制
        body = tank.pymunk_body

        # 导入必要的模块和常量
        import math
        from tank_sprites import PLAYER_MOVEMENT_SPEED, PLAYER_TURN_SPEED

        # 计算Pymunk物理引擎的速度参数（与GameView中的逻辑保持一致）
        PYMUNK_PLAYER_MAX_SPEED = PLAYER_MOVEMENT_SPEED * 60  # 增大移动速度倍率
        PYMUNK_PLAYER_TURN_RAD_PER_SEC = math.radians(PLAYER_TURN_SPEED * 60 * 1.0)  # 增大旋转速度倍率

        # 处理按键按下
        for key in keys_pressed:
            if key == "W":
                # 前进 - 根据Pymunk body的当前角度计算速度向量
                angle_rad = body.angle
                vel_x = math.cos(angle_rad) * PYMUNK_PLAYER_MAX_SPEED
                vel_y = math.sin(angle_rad) * PYMUNK_PLAYER_MAX_SPEED
                body.velocity = (vel_x, vel_y)
            elif key == "S":
                # 后退 - 根据Pymunk body的当前角度计算反向速度向量
                angle_rad = body.angle
                vel_x = -math.cos(angle_rad) * PYMUNK_PLAYER_MAX_SPEED
                vel_y = -math.sin(angle_rad) * PYMUNK_PLAYER_MAX_SPEED
                body.velocity = (vel_x, vel_y)
            elif key == "A":
                # 顺时针旋转 (Pymunk中负角速度是顺时针)
                body.angular_velocity = PYMUNK_PLAYER_TURN_RAD_PER_SEC
            elif key == "D":
                # 逆时针旋转
                body.angular_velocity = -PYMUNK_PLAYER_TURN_RAD_PER_SEC
            elif key == "SPACE":
                # 射击 - 使用与GameView相同的射击逻辑
                if hasattr(self.game_view, 'total_time'):
                    bullet = tank.shoot(self.game_view.total_time)
                    if bullet:  # 只有当shoot返回子弹时才添加
                        self.game_view.bullet_list.append(bullet)
                        if bullet.pymunk_body and bullet.pymunk_shape:
                            self.game_view.space.add(bullet.pymunk_body, bullet.pymunk_shape)
                        # 添加调试信息
                        print(f"🔫 客户端发射子弹: 位置({bullet.center_x:.1f}, {bullet.center_y:.1f}), 角度{bullet.angle:.1f}, 子弹总数: {len(self.game_view.bullet_list)}")
                    else:
                        # 射击失败的调试信息
                        print(f"🚫 客户端射击失败: 冷却时间未到 (当前时间: {self.game_view.total_time:.2f}, 上次射击: {tank.last_shot_time:.2f})")
                else:
                    print("🚫 客户端射击失败: 游戏视图缺少total_time属性")

        # 处理按键释放
        for key in keys_released:
            if key in ["W", "S"]:
                # 停止移动
                body.velocity = (0, 0)
            elif key in ["A", "D"]:
                # 停止旋转
                body.angular_velocity = 0


class ClientGameView(arcade.View):
    """客户端游戏视图 - 重构版"""

    def __init__(self):
        super().__init__()
        self.game_client = GameClient()
        self.game_state = {}
        self.connected = False

        # 游戏阶段
        self.game_phase = "connecting"  # connecting -> playing

        # 游戏视图
        self.game_view = None

        # 断开连接处理标志
        self.should_return_to_browser = False

        # 视图切换保护标志 - 防止重复执行视图切换
        self.is_switching_view = False
        self.scheduled_switch_task = None

        # 游戏初始化标志 - 避免在网络线程中进行OpenGL操作
        self.should_initialize_game = False

        # 地图布局（从主机接收）
        self.received_map_layout = None
        self.received_map_checksum = None
        self.map_sync_verified = False

        # 预创建静态文本对象
        self.connecting_text = arcade.Text(
            "连接中...",
            x=0, y=0,
            color=arcade.color.WHITE,
            font_size=30,
            anchor_x="center"
        )

        self.waiting_text = arcade.Text(
            "等待游戏开始...",
            x=0, y=0,
            color=arcade.color.WHITE,
            font_size=30,
            anchor_x="center"
        )

    def connect_to_room(self, host_ip: str, host_port: int, player_name: str) -> bool:
        """连接到房间"""
        # 设置回调
        self.game_client.set_callbacks(
            connection=self._on_connected,
            disconnection=self._on_disconnected,
            game_state=self._on_game_state_update,
            game_start=self._on_game_start,
            map_sync=self._on_map_sync
        )

        return self.game_client.connect_to_host(host_ip, host_port, player_name)

    def on_show_view(self):
        """显示视图时的初始化"""
        arcade.set_background_color(arcade.color.DARK_BLUE)

    def on_hide_view(self):
        """隐藏视图时的清理"""
        # 清理调度任务
        if self.scheduled_switch_task is not None:
            try:
                arcade.unschedule(self.scheduled_switch_task)
                self.scheduled_switch_task = None
            except Exception as e:
                print(f"清理调度任务时出错: {e}")

        # 重置状态标志
        self.is_switching_view = False
        self.should_return_to_browser = False

        # 断开网络连接
        self.game_client.disconnect()

    def on_draw(self):
        """绘制界面"""
        self.clear()

        if self.game_phase == "connecting":
            # 使用预创建的Text对象绘制连接状态
            self.connecting_text.x = self.window.width // 2
            self.connecting_text.y = self.window.height // 2
            self.connecting_text.draw()

        elif self.game_phase == "waiting":
            # 使用预创建的Text对象绘制等待状态
            self.waiting_text.x = self.window.width // 2
            self.waiting_text.y = self.window.height // 2
            self.waiting_text.draw()

        elif self.game_phase == "playing" and self.game_view:
            # 游戏进行中，委托给游戏视图
            self.game_view.on_draw()

    def on_update(self, _delta_time):
        """更新逻辑"""
        # 检查是否需要返回主菜单（回退机制）
        if self.should_return_to_browser and not self.is_switching_view:
            self.should_return_to_browser = False
            self.is_switching_view = True
            try:
                import game_views
                mode_view = game_views.ModeSelectView()
                self.window.show_view(mode_view)
                print("已返回到主菜单（回退机制）")
                return
            except Exception as e:
                print(f"返回主菜单时出错: {e}")
            finally:
                self.is_switching_view = False

        # 检查是否需要初始化游戏视图（在主线程中安全执行）
        if self.should_initialize_game:
            self.should_initialize_game = False
            try:
                self._initialize_game_view()
            except Exception as e:
                print(f"初始化游戏视图时出错: {e}")

        if self.game_phase == "playing" and self.game_view:
            # 应用服务器状态到本地游戏视图
            self._apply_server_state()

    def on_key_press(self, key, _modifiers):
        """处理按键事件"""
        if key == arcade.key.ESCAPE:
            # 返回主菜单（带保护机制）
            if not self.is_switching_view:
                self.is_switching_view = True
                try:
                    import game_views
                    mode_view = game_views.ModeSelectView()
                    self.window.show_view(mode_view)
                    print("用户按ESC返回主菜单")
                except Exception as e:
                    print(f"ESC返回主菜单时出错: {e}")
                finally:
                    self.is_switching_view = False
        else:
            # 发送按键到服务器
            key_name = self._get_key_name(key)
            if key_name:
                self.game_client.send_key_press(key_name)

    def on_key_release(self, key, _modifiers):
        """处理按键释放事件"""
        key_name = self._get_key_name(key)
        if key_name:
            self.game_client.send_key_release(key_name)

    def _on_connected(self, player_id: str):
        """连接成功回调"""
        self.connected = True
        self.game_phase = "waiting"
        print(f"连接成功，玩家ID: {player_id}")

    def _on_disconnected(self, reason: str):
        """断开连接回调"""
        self.connected = False
        print(f"连接断开: {reason}")

        # 防止重复执行视图切换
        if self.is_switching_view:
            print("视图切换已在进行中，忽略重复请求")
            return

        self.is_switching_view = True

        # 取消之前的调度任务（如果存在）
        if self.scheduled_switch_task is not None:
            try:
                arcade.unschedule(self.scheduled_switch_task)
                self.scheduled_switch_task = None
            except Exception as e:
                print(f"取消之前的调度任务时出错: {e}")

        # 延迟视图切换，避免在网络线程中直接操作OpenGL
        # 使用arcade的调度器在主线程中执行视图切换
        try:
            def switch_view(delta_time):
                """切换到主菜单视图

                Args:
                    delta_time: arcade.schedule() 传递的时间参数
                """
                try:
                    if hasattr(self, 'window') and self.window and not self.window.invalid:
                        # 直接返回到主菜单，避免房间浏览器的循环问题
                        import game_views
                        mode_view = game_views.ModeSelectView()
                        self.window.show_view(mode_view)
                        print("已返回到主菜单")

                    # 清理调度任务
                    if self.scheduled_switch_task is not None:
                        arcade.unschedule(self.scheduled_switch_task)
                        self.scheduled_switch_task = None

                except Exception as e:
                    print(f"执行视图切换时出错: {e}")
                    # 如果切换失败，设置回退标志
                    self.should_return_to_browser = True
                finally:
                    # 重置切换标志
                    self.is_switching_view = False

            # 保存调度任务引用
            self.scheduled_switch_task = switch_view
            # 在主线程中执行视图切换
            arcade.schedule(switch_view, 0.1)

        except Exception as e:
            print(f"调度视图切换时出错: {e}")
            # 如果调度失败，设置一个标志让主循环处理
            self.should_return_to_browser = True
            self.is_switching_view = False

    def _on_game_start(self, game_config: dict):
        """游戏开始回调"""
        print("收到游戏开始消息")

        # 保存地图布局
        if "map_layout" in game_config:
            self._process_received_map(game_config["map_layout"], game_config.get("map_checksum"))

        # 设置标志在主线程中初始化游戏视图
        if self.game_phase == "waiting":
            self.should_initialize_game = True

    def _on_game_state_update(self, state: dict):
        """游戏状态更新回调"""
        self.game_state = state

    def _process_received_map(self, map_layout: list, map_checksum: str = None):
        """处理接收到的地图数据"""
        from .map_sync import MapSyncManager

        try:
            # 验证地图数据
            if not MapSyncManager.validate_map_layout(map_layout):
                print("❌ 接收到的地图数据无效")
                return

            # 验证校验和（如果提供）
            if map_checksum:
                actual_checksum = MapSyncManager.calculate_map_checksum(map_layout)
                if actual_checksum != map_checksum:
                    print(f"❌ 地图校验和不匹配: 期望 {map_checksum[:8]}..., 实际 {actual_checksum[:8]}...")
                    return
                else:
                    print(f"✅ 地图校验和验证通过: {actual_checksum[:8]}...")
                    self.map_sync_verified = True

            # 保存地图数据
            self.received_map_layout = map_layout
            self.received_map_checksum = map_checksum

            # 获取地图信息
            map_info = MapSyncManager.get_map_info(map_layout)
            print(f"✅ 地图数据已接收: {map_info['wall_count']} 个墙壁")

        except Exception as e:
            print(f"❌ 处理地图数据时出错: {e}")

    def _on_map_sync(self, map_data: dict):
        """处理地图同步消息"""
        print("收到地图同步消息")

        if "map_layout" in map_data:
            self._process_received_map(
                map_data["map_layout"],
                map_data.get("map_checksum")
            )

    def _initialize_game_view(self):
        """初始化游戏视图"""
        import game_views
        from .map_sync import MapSyncManager

        # 检查是否已接收到地图数据
        if not self.received_map_layout:
            print("❌ 尚未接收到地图数据，无法初始化游戏")
            return

        # 再次验证地图数据
        if not MapSyncManager.validate_map_layout(self.received_map_layout):
            print("❌ 地图数据验证失败，无法初始化游戏")
            return

        self.game_view = game_views.GameView(mode="network_client")

        # 设置固定地图
        self.game_view.set_map_layout(self.received_map_layout)

        # 验证地图是否正确设置
        current_map = self.game_view.get_map_layout()
        if MapSyncManager.compare_maps(current_map, self.received_map_layout):
            print(f"✅ 地图同步成功: {len(self.received_map_layout)} 个墙壁")
        else:
            print("❌ 地图同步失败，地图数据不匹配")
            return

        # 重要：调用setup方法初始化游戏元素，包括player_list
        self.game_view.setup()

        self.game_phase = "playing"
        print("🎮 客户端游戏开始！")

    def _apply_server_state(self):
        """应用服务器状态到本地游戏视图"""
        if not self.game_view or not self.game_state:
            return

        # 更新坦克状态
        tanks_data = self.game_state.get("tanks", [])
        if hasattr(self.game_view, 'player_list') and self.game_view.player_list is not None:
            try:
                for i, tank_data in enumerate(tanks_data):
                    if i < len(self.game_view.player_list):
                        tank = self.game_view.player_list[i]
                        if tank is not None:  # 确保坦克对象不为None
                            tank.center_x = tank_data.get("x", tank.center_x)
                            tank.center_y = tank_data.get("y", tank.center_y)
                            tank.angle = tank_data.get("angle", tank.angle)
                            if hasattr(tank, 'health'):
                                tank.health = tank_data.get("health", tank.health)
                            # 更新坦克图片文件信息（用于子弹颜色计算）
                            if "tank_image_file" in tank_data and tank_data["tank_image_file"]:
                                tank.tank_image_file = tank_data["tank_image_file"]
                            # 更新玩家ID（用于子弹所有者匹配）
                            if "player_id" in tank_data:
                                tank.player_id = tank_data["player_id"]
            except Exception as e:
                print(f"应用坦克状态时出错: {e}")

        # 更新子弹状态 - 优化子弹同步问题
        bullets_data = self.game_state.get("bullets", [])
        if hasattr(self.game_view, 'bullet_list') and self.game_view.bullet_list is not None:
            try:
                # 优化：只在子弹数量发生变化时才重建子弹列表
                current_bullet_count = len(self.game_view.bullet_list)
                server_bullet_count = len(bullets_data)

                # 如果子弹数量没有变化，只更新位置
                if current_bullet_count == server_bullet_count and current_bullet_count > 0:
                    # 更新现有子弹的位置
                    for i, bullet_data in enumerate(bullets_data):
                        if i < len(self.game_view.bullet_list):
                            bullet = self.game_view.bullet_list[i]
                            if bullet is not None:
                                bullet.center_x = bullet_data.get("x", bullet.center_x)
                                bullet.center_y = bullet_data.get("y", bullet.center_y)
                                bullet.angle = bullet_data.get("angle", bullet.angle)
                                # 同步到物理体
                                if bullet.pymunk_body:
                                    bullet.pymunk_body.position = (bullet.center_x, bullet.center_y)
                else:
                    # 子弹数量发生变化，需要重建子弹列表
                    # 清除现有子弹（避免重复和过期子弹）
                    if hasattr(self.game_view, 'space') and self.game_view.space:
                        # 从物理空间中移除旧子弹
                        for bullet in self.game_view.bullet_list:
                            if bullet and hasattr(bullet, 'pymunk_body') and bullet.pymunk_body:
                                try:
                                    if bullet.pymunk_body in self.game_view.space.bodies:
                                        self.game_view.space.remove(bullet.pymunk_body)
                                    if hasattr(bullet, 'pymunk_shape') and bullet.pymunk_shape:
                                        if bullet.pymunk_shape in self.game_view.space.shapes:
                                            self.game_view.space.remove(bullet.pymunk_shape)
                                except Exception as e:
                                    print(f"移除旧子弹物理体时出错: {e}")

                    # 清空子弹列表
                    self.game_view.bullet_list.clear()

                    # 根据服务器数据创建新子弹（只在重建时执行）
                    for bullet_data in bullets_data:
                        try:
                            from tank_sprites import Bullet

                            bullet_x = bullet_data.get("x", 0)
                            bullet_y = bullet_data.get("y", 0)
                            bullet_angle = bullet_data.get("angle", 0)
                            bullet_owner = bullet_data.get("owner", "unknown")

                            # 根据子弹所有者确定正确的子弹颜色
                            bullet_color = self._get_bullet_color_for_owner(bullet_owner)

                            # 使用标准子弹半径（与tank_sprites.py保持一致）
                            BULLET_RADIUS = 4

                            # 创建子弹对象（客户端显示用，不需要完整的物理模拟）
                            bullet = Bullet(
                                radius=BULLET_RADIUS,  # 使用标准子弹半径
                                owner=None,  # 客户端显示用，不需要owner引用
                                tank_center_x=bullet_x,
                                tank_center_y=bullet_y,
                                actual_emission_angle_degrees=bullet_angle,
                                speed_magnitude=0,  # 客户端不需要速度，位置由服务器控制
                                color=bullet_color  # 根据所有者确定的颜色
                            )

                            # 设置子弹位置（覆盖构造函数中的物理计算）
                            bullet.center_x = bullet_x
                            bullet.center_y = bullet_y
                            bullet.angle = bullet_angle

                            # 添加到子弹列表
                            self.game_view.bullet_list.append(bullet)

                            # 将子弹添加到物理空间（用于渲染，但不参与物理模拟）
                            if hasattr(self.game_view, 'space') and self.game_view.space:
                                if bullet.pymunk_body and bullet.pymunk_shape:
                                    # 设置子弹为静态（不受物理影响）
                                    bullet.pymunk_body.velocity = (0, 0)
                                    bullet.pymunk_body.angular_velocity = 0
                                    self.game_view.space.add(bullet.pymunk_body, bullet.pymunk_shape)

                        except Exception as e:
                            print(f"创建客户端子弹时出错: {e}")

            except Exception as e:
                print(f"应用子弹状态时出错: {e}")

        # 更新分数
        scores = self.game_state.get("scores", {})
        if hasattr(self.game_view, 'player1_score') and "host" in scores:
            self.game_view.player1_score = scores["host"]
        if hasattr(self.game_view, 'player2_score') and "client" in scores:
            self.game_view.player2_score = scores["client"]

        # 更新回合状态信息
        round_info = self.game_state.get("round_info", {})
        if round_info:
            if hasattr(self.game_view, 'round_over') and "round_over" in round_info:
                self.game_view.round_over = round_info["round_over"]
            if hasattr(self.game_view, 'round_over_timer') and "round_over_timer" in round_info:
                self.game_view.round_over_timer = round_info["round_over_timer"]
            if hasattr(self.game_view, 'round_result_text') and "round_result_text" in round_info:
                self.game_view.round_result_text = round_info["round_result_text"]

    def _get_bullet_color_for_owner(self, owner_id: str):
        """根据子弹所有者确定子弹颜色（与tank_sprites.py中的逻辑保持一致）"""
        import arcade

        # 默认颜色
        bullet_color = arcade.color.YELLOW_ORANGE

        # 根据所有者ID找到对应的坦克
        if hasattr(self.game_view, 'player_list') and self.game_view.player_list is not None:
            for tank in self.game_view.player_list:
                if tank is not None and hasattr(tank, 'player_id'):
                    if getattr(tank, 'player_id', None) == owner_id:
                        # 找到对应的坦克，根据其图片文件确定颜色
                        if hasattr(tank, 'tank_image_file') and tank.tank_image_file:
                            path = tank.tank_image_file.lower()
                            if 'green' in path:
                                bullet_color = (0, 255, 0)  # 绿色
                            elif 'desert' in path:
                                bullet_color = (255, 165, 0)  # 沙漠色
                            elif 'grey' in path:
                                bullet_color = (128, 128, 128)  # 灰色
                            elif 'blue' in path:
                                bullet_color = (0, 0, 128)  # 蓝色
                        break

        # 如果没有找到对应坦克，根据owner_id使用默认颜色方案
        if owner_id == "host":
            bullet_color = (0, 255, 0)  # 主机默认绿色
        elif owner_id.startswith("client"):
            bullet_color = (0, 0, 128)  # 客户端默认蓝色

        return bullet_color

    def _get_key_name(self, key) -> str:
        """将arcade按键转换为字符串"""
        key_map = {
            arcade.key.W: "W",
            arcade.key.A: "A",
            arcade.key.S: "S",
            arcade.key.D: "D",
            arcade.key.SPACE: "SPACE",
            arcade.key.UP: "UP",
            arcade.key.DOWN: "DOWN",
            arcade.key.LEFT: "LEFT",
            arcade.key.RIGHT: "RIGHT"
        }
        return key_map.get(key, "")
