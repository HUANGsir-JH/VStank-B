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
        
        # 开始房间发现
        self.room_discovery.start_discovery(self._on_rooms_updated)
        print("开始搜索房间...")
    
    def on_hide_view(self):
        """隐藏视图时的清理"""
        self.room_discovery.stop_discovery()
    
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

        # 创建游戏视图
        self.game_view = game_views.GameView(mode="network_host")

        # 重要：调用setup方法初始化游戏元素，包括player_list
        self.game_view.setup()

        self.game_phase = "playing"

        print("游戏开始！")

        # 获取地图布局并发送给客户端
        map_layout = self.game_view.get_map_layout()

        # 通知客户端游戏开始，包含地图布局
        start_msg = MessageFactory.create_game_start({
            "map_layout": map_layout
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
                            "health": getattr(tank, 'health', 5)
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

        # 提取分数
        scores = {}
        if hasattr(self.game_view, 'player1_score'):
            scores["host"] = self.game_view.player1_score
        if hasattr(self.game_view, 'player2_score'):
            scores["client"] = self.game_view.player2_score

        return {
            "tanks": tanks,
            "bullets": bullets,
            "scores": scores
        }

    def _apply_client_input(self, _client_id: str, keys_pressed: list, keys_released: list):
        """应用客户端输入到游戏中"""
        if not self.game_view or not hasattr(self.game_view, 'player2_tank'):
            return

        # 假设客户端控制player2_tank
        tank = self.game_view.player2_tank
        if not tank:
            return

        # 处理按键
        for key in keys_pressed:
            if key == "W":
                tank.speed = tank.max_speed
            elif key == "S":
                tank.speed = -tank.max_speed
            elif key == "A":
                tank.angle_speed = tank.turn_speed_degrees
            elif key == "D":
                tank.angle_speed = -tank.turn_speed_degrees
            elif key == "SPACE":
                # 射击
                if hasattr(self.game_view, '_handle_tank_shooting'):
                    self.game_view._handle_tank_shooting(tank)

        for key in keys_released:
            if key in ["W", "S"]:
                tank.speed = 0
            elif key in ["A", "D"]:
                tank.angle_speed = 0


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

        # 游戏初始化标志 - 避免在网络线程中进行OpenGL操作
        self.should_initialize_game = False

        # 地图布局（从主机接收）
        self.received_map_layout = None

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
            game_start=self._on_game_start
        )

        return self.game_client.connect_to_host(host_ip, host_port, player_name)

    def on_show_view(self):
        """显示视图时的初始化"""
        arcade.set_background_color(arcade.color.DARK_BLUE)

    def on_hide_view(self):
        """隐藏视图时的清理"""
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
        # 检查是否需要返回房间浏览器
        if self.should_return_to_browser:
            self.should_return_to_browser = False
            try:
                browser_view = RoomBrowserView()
                self.window.show_view(browser_view)
                return
            except Exception as e:
                print(f"返回房间浏览器时出错: {e}")

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
            # 返回房间浏览
            browser_view = RoomBrowserView()
            self.window.show_view(browser_view)
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

        # 延迟视图切换，避免在网络线程中直接操作OpenGL
        # 使用arcade的调度器在主线程中执行视图切换
        try:
            def switch_view():
                if hasattr(self, 'window') and self.window:
                    browser_view = RoomBrowserView()
                    self.window.show_view(browser_view)

            # 在主线程中执行视图切换
            arcade.schedule(switch_view, 0.1)
        except Exception as e:
            print(f"切换视图时出错: {e}")
            # 如果调度失败，设置一个标志让主循环处理
            self.should_return_to_browser = True

    def _on_game_start(self, game_config: dict):
        """游戏开始回调"""
        print("收到游戏开始消息")

        # 保存地图布局
        if "map_layout" in game_config:
            self.received_map_layout = game_config["map_layout"]
            print(f"收到地图布局: {len(self.received_map_layout)} 个墙壁")

        # 设置标志在主线程中初始化游戏视图
        if self.game_phase == "waiting":
            self.should_initialize_game = True

    def _on_game_state_update(self, state: dict):
        """游戏状态更新回调"""
        self.game_state = state

    def _initialize_game_view(self):
        """初始化游戏视图"""
        import game_views

        self.game_view = game_views.GameView(mode="network_client")

        # 如果收到了地图布局，设置固定地图
        if self.received_map_layout:
            self.game_view.set_map_layout(self.received_map_layout)
            print(f"应用接收到的地图布局: {len(self.received_map_layout)} 个墙壁")

        # 重要：调用setup方法初始化游戏元素，包括player_list
        self.game_view.setup()

        self.game_phase = "playing"
        print("游戏开始！")

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
            except Exception as e:
                print(f"应用坦克状态时出错: {e}")

        # 更新分数
        scores = self.game_state.get("scores", {})
        if hasattr(self.game_view, 'player1_score') and "host" in scores:
            self.game_view.player1_score = scores["host"]
        if hasattr(self.game_view, 'player2_score') and "client" in scores:
            self.game_view.player2_score = scores["client"]

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
