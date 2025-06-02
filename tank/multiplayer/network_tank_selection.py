"""
多人游戏坦克选择视图

为多人游戏提供坦克选择界面，支持主机和客户端的坦克选择
实现坦克选择的网络同步和互斥机制
"""

import arcade
from typing import Optional, Dict, Any, List, Callable
import sys
import os

# 添加父目录到路径以导入tank_selection
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tank_selection import TankOption, PLAYER_IMAGE_PATH_GREEN, PLAYER_IMAGE_PATH_DESERT, PLAYER_IMAGE_PATH_BLUE, PLAYER_IMAGE_PATH_GREY
from .udp_messages import MessageFactory, MessageType, UDPMessage
from typing import Dict


# 如果constants模块不存在，使用默认值
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720


class NetworkTankSelectionView(arcade.View):
    """多人游戏坦克选择视图 - 支持网络同步"""

    def __init__(self, is_host: bool = True, room_name: str = "",
                 host_ip: str = "", host_port: int = 12346,
                 game_host=None, game_client=None):
        super().__init__()
        self.is_host = is_host
        self.room_name = room_name
        self.host_ip = host_ip
        self.host_port = host_port

        # 网络对象引用
        self.game_host = game_host
        self.game_client = game_client

        # 坦克选择相关
        self.tank_sprites = arcade.SpriteList()
        self.tank_options = []
        self.selected_tank = None
        self.my_player_id = "host" if is_host else None

        # 全局坦克选择状态 (主机维护，客户端接收同步)
        self.selected_tanks = {}  # {player_id: {"tank_type": str, "tank_image_path": str}}
        self.ready_players = set()  # 已准备的玩家ID集合
        self.connected_players = set()  # 已连接的玩家ID集合

        # 可选坦克类型
        self.available_tank_types = ["green", "yellow", "blue", "grey"]
        self.tank_type_to_image = {
            "green": PLAYER_IMAGE_PATH_GREEN,
            "yellow": PLAYER_IMAGE_PATH_DESERT,
            "blue": PLAYER_IMAGE_PATH_BLUE,
            "grey": PLAYER_IMAGE_PATH_GREY
        }

        # 网络状态
        self.ready_to_start = False
        self.selection_conflict_message = ""  # 冲突提示消息
        self.conflict_message_timer = 0.0  # 冲突消息显示计时器

        # 设置网络回调
        self._setup_network_callbacks()

    def _setup_network_callbacks(self):
        """设置网络回调函数"""
        if self.is_host and self.game_host:
            # 主机端：设置坦克选择消息处理回调
            self.game_host.set_tank_selection_callback(self._handle_client_tank_selection)
        elif not self.is_host and self.game_client:
            # 客户端：设置坦克选择同步回调
            self.game_client.set_tank_selection_callback(self._handle_tank_selection_sync)

    def setup(self):
        """设置坦克选择界面"""
        # 创建坦克选项（复用单人游戏的逻辑）
        center_y = SCREEN_HEIGHT / 2
        start_x = SCREEN_WIDTH / 2 - 300  # 居中显示
        padding = 150

        self.tank_options = [
            TankOption(PLAYER_IMAGE_PATH_GREEN, "绿色坦克", start_x, center_y, 0.1),
            TankOption(PLAYER_IMAGE_PATH_DESERT, "黄色坦克", start_x + padding, center_y, 0.11),
            TankOption(PLAYER_IMAGE_PATH_BLUE, "蓝色坦克", start_x + 2 * padding, center_y, 0.1),
            TankOption(PLAYER_IMAGE_PATH_GREY, "灰色坦克", start_x + 3 * padding, center_y, 0.1)
        ]

        # 将坦克精灵添加到列表
        for option in self.tank_options:
            self.tank_sprites.append(option.sprite)

        # 默认选择第一个坦克
        self.selected_tank = self.tank_options[0]
        self.selected_tank.selected = True
        self.selected_tank.player = 1

        # 初始化连接的玩家列表
        if self.is_host:
            self.connected_players.add("host")
            self.my_player_id = "host"
            # 主机默认选择第一个坦克
            self._select_tank("green", broadcast=False)
        else:
            # 客户端获取自己的玩家ID
            if self.game_client:
                self.my_player_id = self.game_client.get_player_id()
                if self.my_player_id:
                    self.connected_players.add(self.my_player_id)

    def on_show_view(self):
        """显示视图时的设置"""
        arcade.set_background_color(arcade.color.LIGHT_BLUE)
        self.setup()

    def on_draw(self):
        """绘制视图"""
        self.clear()

        # 绘制标题
        title = "选择你的坦克 - 多人游戏"
        if self.is_host:
            title += " (主机)"
        else:
            title += " (客户端)"

        arcade.draw_text(
            title,
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT - 80,
            arcade.color.BLACK,
            font_size=32,
            anchor_x="center"
        )

        # 绘制房间信息
        if self.is_host:
            room_info = f"房间: {self.room_name} | 玩家: {len(self.connected_players)}"
        else:
            room_info = f"连接到: {self.host_ip}:{self.host_port}"

        arcade.draw_text(
            room_info,
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT - 120,
            arcade.color.DARK_BLUE,
            font_size=16,
            anchor_x="center"
        )

        # 绘制坦克选择区域
        self._draw_tank_selection_area()

        # 绘制玩家状态信息
        self._draw_player_status()

        # 绘制操作说明
        arcade.draw_text(
            "A/D 选择坦克 | SPACE 确认准备 | ESC 返回",
            SCREEN_WIDTH / 2,
            80,
            arcade.color.BLACK,
            font_size=16,
            anchor_x="center"
        )

        # 绘制冲突消息
        if self.selection_conflict_message and self.conflict_message_timer > 0:
            arcade.draw_text(
                self.selection_conflict_message,
                SCREEN_WIDTH / 2,
                50,
                arcade.color.RED,
                font_size=18,
                anchor_x="center",
                bold=True
            )

    def _draw_tank_selection_area(self):
        """绘制坦克选择区域"""
        center_y = SCREEN_HEIGHT / 2
        start_x = SCREEN_WIDTH / 2 - 300
        padding = 150
        self.tank_sprites.draw()
        for i, tank_type in enumerate(self.available_tank_types):
            x_pos = start_x + i * padding

            # 检查这个坦克是否被选择
            tank_owner = None
            for player_id, tank_info in self.selected_tanks.items():
                if tank_info.get("tank_type") == tank_type:
                    tank_owner = player_id
                    break

            # 绘制坦克图像
            try:
                tank_sprite = self.tank_sprites[i]
                tank_width = tank_sprite.width
                tank_height = tank_sprite.height

                # 绘制选择状态
                if tank_owner:
                    # 已被选择 - 绘制边框和玩家标识
                    border_color = arcade.color.GREEN if tank_owner == self.my_player_id else arcade.color.RED
                    arcade.draw_lrbt_rectangle_outline(
                        x_pos - tank_width//2 - 5, x_pos + tank_width//2 + 5,
                        center_y - tank_height//2 - 5, center_y + tank_height//2 + 5,
                        border_color, 3
                    )

                    # 显示玩家标识
                    player_text = "你" if tank_owner == self.my_player_id else f"玩家{tank_owner[-4:]}"
                    arcade.draw_text(
                        player_text,
                        x_pos, center_y - tank_height//2 - 25,
                        border_color, font_size=12, anchor_x="center", bold=True
                    )
                elif self.selected_tank and self._get_tank_type(self.selected_tank.image_path) == tank_type:
                    # 当前预选择 - 绘制虚线边框
                    arcade.draw_lrbt_rectangle_outline(
                        x_pos - tank_width//2 - 3, x_pos + tank_width//2 + 3,
                        center_y - tank_height//2 - 3, center_y + tank_height//2 + 3,
                        arcade.color.YELLOW, 2
                    )

            except Exception as e:
                print(f"加载坦克图片失败 {tank_type}: {e}")
                # 备用颜色方块
                color_map = {
                    "green": arcade.color.GREEN,
                    "yellow": arcade.color.YELLOW,
                    "blue": arcade.color.BLUE,
                    "grey": arcade.color.GRAY
                }
                color = color_map.get(tank_type, arcade.color.WHITE)
                arcade.draw_lrbt_rectangle_filled(
                    x_pos - 25, x_pos + 25, center_y - 25, center_y + 25, color
                )

            # 坦克名称
            tank_names = {
                "green": "绿色坦克",
                "yellow": "黄色坦克",
                "blue": "蓝色坦克",
                "grey": "灰色坦克"
            }
            arcade.draw_text(
                tank_names.get(tank_type, tank_type),
                x_pos, center_y - 80,
                arcade.color.BLACK, font_size=12, anchor_x="center"
            )

    def _draw_player_status(self):
        """绘制玩家状态信息"""
        y_start = 250

        # 显示所有玩家的准备状态
        arcade.draw_text(
            "玩家状态:",
            50, y_start,
            arcade.color.BLACK, font_size=16, bold=True
        )

        y_pos = y_start - 30
        for player_id in self.connected_players:
            is_ready = player_id in self.ready_players
            status_text = "✓ 已准备" if is_ready else "○ 未准备"
            status_color = arcade.color.GREEN if is_ready else arcade.color.ORANGE

            player_name = "你" if player_id == self.my_player_id else f"玩家{player_id[-4:]}"

            arcade.draw_text(
                f"{player_name}: {status_text}",
                50, y_pos,
                status_color, font_size=14
            )
            y_pos -= 25

    def on_update(self, delta_time):
        """更新逻辑"""
        # 更新冲突消息计时器
        if self.conflict_message_timer > 0:
            self.conflict_message_timer -= delta_time
            if self.conflict_message_timer <= 0:
                self.selection_conflict_message = ""

    def on_key_press(self, key, modifiers):
        """处理按键事件"""
        if key == arcade.key.ESCAPE:
            # 返回上一级视图
            self._return_to_previous_view()

        elif key == arcade.key.A:
            # 向左选择坦克
            self._change_tank_selection(-1)

        elif key == arcade.key.D:
            # 向右选择坦克
            self._change_tank_selection(1)

        elif key == arcade.key.SPACE:
            # 确认坦克选择并准备
            self._confirm_tank_selection()

    def _change_tank_selection(self, direction: int):
        """改变坦克选择"""
        if self.ready_to_start:
            return  # 已准备的玩家不能再改变选择

        if not self.selected_tank:
            return

        # 找到当前选择的索引
        current_index = self.tank_options.index(self.selected_tank)
        new_index = (current_index + direction) % len(self.tank_options)

        # 取消当前选择
        self.selected_tank.selected = False
        self.selected_tank.player = None

        # 设置新选择
        self.selected_tank = self.tank_options[new_index]
        self.selected_tank.selected = True
        self.selected_tank.player = 1

    def _confirm_tank_selection(self):
        """确认坦克选择并准备"""
        if self.ready_to_start:
            return  # 已经准备了

        if not self.selected_tank:
            return

        tank_type = self._get_tank_type(self.selected_tank.image_path)
        tank_image_path = self.selected_tank.image_path

        # 检查坦克是否已被其他玩家选择
        if self._is_tank_taken(tank_type):
            self._show_conflict_message(f"坦克 {tank_type} 已被其他玩家选择！")
            return

        # 选择坦克
        self._select_tank(tank_type, tank_image_path, broadcast=True)

        # 设置准备状态
        self.ready_to_start = True
        self.ready_players.add(self.my_player_id)

        # 发送准备消息
        if self.is_host:
            self._broadcast_tank_selection_sync()
            self._check_all_players_ready()
        else:
            self._send_tank_selection_ready(tank_type, tank_image_path)

    def _get_tank_type(self, image_path: str) -> str:
        """根据图片路径获取坦克类型"""
        if 'green' in image_path.lower():
            return "green"
        elif 'desert' in image_path.lower() or 'yellow' in image_path.lower():
            return "yellow"
        elif 'blue' in image_path.lower():
            return "blue"
        elif 'grey' in image_path.lower():
            return "grey"
        return "green"

    def _is_tank_taken(self, tank_type: str) -> bool:
        """检查坦克是否已被其他玩家选择"""
        for player_id, tank_info in self.selected_tanks.items():
            if player_id != self.my_player_id and tank_info.get("tank_type") == tank_type:
                return True
        return False

    def _select_tank(self, tank_type: str, tank_image_path: str = None, broadcast: bool = True):
        """选择坦克"""
        if not tank_image_path:
            tank_image_path = self.tank_type_to_image.get(tank_type, "")

        self.selected_tanks[self.my_player_id] = {
            "tank_type": tank_type,
            "tank_image_path": tank_image_path
        }

        if broadcast and self.is_host:
            self._broadcast_tank_selection_sync()

    def _show_conflict_message(self, message: str):
        """显示冲突消息"""
        self.selection_conflict_message = message
        self.conflict_message_timer = 3.0  # 显示3秒

    def _return_to_previous_view(self):
        """返回上一级视图"""
        if self.is_host:
            from .network_views import NetworkHostView
            host_view = NetworkHostView()
            host_view.game_host = self.game_host  # 传递网络对象
            self.window.show_view(host_view)
        else:
            from .network_views import RoomBrowserView
            browser_view = RoomBrowserView()
            self.window.show_view(browser_view)

    # === 网络通信方法 ===

    def _broadcast_tank_selection_sync(self):
        """主机广播坦克选择状态同步"""
        if not self.is_host or not self.game_host:
            return

        message = MessageFactory.create_tank_selection_sync(
            self.selected_tanks, list(self.ready_players)
        )

        # 通过主机广播给所有客户端
        self.game_host.broadcast_message(message)

    def _send_tank_selection_ready(self, tank_type: str, tank_image_path: str):
        """客户端发送准备完成消息"""
        if self.is_host or not self.game_client:
            return

        message = MessageFactory.create_tank_selection_ready(
            self.my_player_id, tank_type, tank_image_path
        )

        self.game_client.send_message(message)

    def _check_all_players_ready(self):
        """检查是否所有玩家都已准备完成"""
        if not self.is_host:
            return

        # 检查所有连接的玩家是否都已准备
        if len(self.ready_players) >= len(self.connected_players):
            print("所有玩家已准备完成，开始游戏！")
            self._start_game()

    def _start_game(self):
        """开始游戏"""
        if not self.is_host:
            return

        # 收集所有玩家的坦克信息
        tank_selections = {}
        for player_id, tank_info in self.selected_tanks.items():
            tank_selections[player_id] = tank_info

        # 切换到游戏视图
        from .network_views import NetworkHostView
        host_view = NetworkHostView()
        host_view.game_host = self.game_host  # 传递现有的game_host实例
        host_view.tank_selections = tank_selections  # 传递坦克选择信息
        host_view.game_phase = "playing"  # 直接设置为playing阶段
        
        # 正确传递所有网络回调
        if self.game_host:
            host_view.set_callbacks(
                client_join=self._on_client_join,
                client_leave=self._on_client_leave,
                input_received=self._on_input_received,
                game_state=self._get_game_state
            )
        
        host_view.start_game_directly()  # 开始游戏
        host_view.on_show_view()  # 显式调用on_show_view

    # === 网络回调处理方法 ===

    def _handle_client_tank_selection(self, client_id: str, message_type: str, data: dict):
        """处理客户端的坦克选择消息（主机端）"""
        if not self.is_host:
            return

        if message_type == MessageType.TANK_SELECTED:
            tank_type = data.get("tank_type")
            tank_image_path = data.get("tank_image_path")

            # 检查坦克是否已被选择
            if self._is_tank_taken_by_others(tank_type, client_id):
                # 发送冲突消息
                conflict_msg = MessageFactory.create_tank_selection_conflict(
                    client_id, tank_type, "坦克已被其他玩家选择"
                )
                self.game_host.send_to_client(client_id, conflict_msg)
                return

            # 更新客户端的坦克选择
            self.selected_tanks[client_id] = {
                "tank_type": tank_type,
                "tank_image_path": tank_image_path
            }

            # 广播更新
            self._broadcast_tank_selection_sync()

        elif message_type == MessageType.TANK_SELECTION_READY:
            tank_type = data.get("tank_type")
            tank_image_path = data.get("tank_image_path")

            # 最终检查坦克是否可用
            if self._is_tank_taken_by_others(tank_type, client_id):
                conflict_msg = MessageFactory.create_tank_selection_conflict(
                    client_id, tank_type, "坦克已被其他玩家选择"
                )
                self.game_host.send_to_client(client_id, conflict_msg)
                return

            # 确认客户端的坦克选择和准备状态
            self.selected_tanks[client_id] = {
                "tank_type": tank_type,
                "tank_image_path": tank_image_path
            }
            self.ready_players.add(client_id)
            self.connected_players.add(client_id)

            # 广播更新
            self._broadcast_tank_selection_sync()

            # 检查是否所有玩家都准备完成
            self._check_all_players_ready()

    def _handle_tank_selection_sync(self, message_type: str, data: dict):
        """处理坦克选择同步消息（客户端）"""
        if self.is_host:
            return

        if message_type == MessageType.TANK_SELECTION_SYNC:
            # 更新全局坦克选择状态
            self.selected_tanks = data.get("selected_tanks", {})
            self.ready_players = set(data.get("ready_players", []))

        elif message_type == MessageType.TANK_SELECTION_CONFLICT:
            # 显示冲突消息
            reason = data.get("reason", "选择冲突")
            self._show_conflict_message(reason)

            # 重置准备状态
            self.ready_to_start = False
            if self.my_player_id in self.ready_players:
                self.ready_players.remove(self.my_player_id)

    def _is_tank_taken_by_others(self, tank_type: str, exclude_player_id: str) -> bool:
        """检查坦克是否被其他玩家选择（排除指定玩家）"""
        for player_id, tank_info in self.selected_tanks.items():
            if player_id != exclude_player_id and tank_info.get("tank_type") == tank_type:
                return True
        return False
