import arcade
import math
import os
from tank_sprites import (
    PLAYER_IMAGE_PATH_GREEN, PLAYER_IMAGE_PATH_DESERT,
    PLAYER_IMAGE_PATH_BLUE, PLAYER_IMAGE_PATH_GREY
)

# --- 常量 ---
SCREEN_WIDTH = 1280  
SCREEN_HEIGHT = 720

class TankOption:
    """坦克选择选项类"""    
    def __init__(self, image_path, name, center_x, center_y, scale=0.8):
        self.sprite = arcade.Sprite(image_path, scale)
        self.sprite.center_x = center_x
        self.sprite.center_y = center_y
        self.name = name
        self.image_path = image_path
        self.selected = False
        self.player = None  # 哪个玩家选择了这个坦克 (1 或 2)
    def draw(self):
        """绘制坦克选项及其选中状态"""
        # 坦克精灵将由TankSelectionView的SpriteList绘制
        # 这里只绘制附加的文字和边框等元素

        # 绘制坦克名称
        arcade.draw_text(
            self.name,
            self.sprite.center_x,
            self.sprite.center_y - 100,
            arcade.color.BLACK,
            font_size=16,
            anchor_x="center"
        )

        # 如果被选中，绘制指示框和玩家标识
        if self.selected or self.player:
            # 计算边界框坐标
            left = self.sprite.center_x - self.sprite.width / 1.5-3
            right = self.sprite.center_x + self.sprite.width / 1.5+3
            bottom = self.sprite.center_y - 60-3
            top = self.sprite.center_y + self.sprite.height / 1.5+3
            
            # 选中边框颜色根据玩家不同
            border_color = arcade.color.GREEN if self.player == 1 else arcade.color.RED
            
            # 绘制选中边框
            arcade.draw_lrbt_rectangle_outline( # 修正拼写错误
                left, right, bottom, top, # 参数顺序是 left, right, bottom, top
                border_color,
                border_width=3
            )
            
            # 绘制玩家标识 (数字)
            box_center_x = self.sprite.center_x
            box_center_y = self.sprite.center_y + self.sprite.height / 2 + 20 # 在坦克上方一定距离
            
            # 绘制玩家编号数字
            arcade.draw_text(
                str(self.player), # 绘制数字
                box_center_x,
                box_center_y+20,
                arcade.color.WHITE, # 尝试使用白色，更醒目
                font_size=24, 
                anchor_x="center",
                anchor_y="center", 
                bold=True
            )


class TankSelectionView(arcade.View):
    """坦克选择视图"""    
    def __init__(self):
        super().__init__()
        self.tank_options = []
        self.player1_selection = None
        self.player2_selection = None
        self.ready_to_start = False
        # 创建一个SpriteList来管理所有坦克精灵
        self.tank_sprites = arcade.SpriteList()
        # 初始化坦克选项
        self._setup_tank_options()
    def _setup_tank_options(self):
        """设置坦克选项"""
        # 计算四个坦克的位置
        padding = 200  # 坦克之间的间距
        total_width = 3 * padding  # 三个间距对应四个坦克
        start_x = (SCREEN_WIDTH - total_width) / 2
        center_y = SCREEN_HEIGHT / 2
        
        # 创建四种坦克选项
        self.tank_options = [
            TankOption(PLAYER_IMAGE_PATH_GREEN, "绿色坦克", start_x, center_y, 0.1),
            TankOption(PLAYER_IMAGE_PATH_DESERT, "黄色坦克", start_x + padding, center_y, 0.11),
            TankOption(PLAYER_IMAGE_PATH_BLUE, "蓝色坦克", start_x + 2 * padding, center_y, 0.1),
            TankOption(PLAYER_IMAGE_PATH_GREY, "灰色坦克", start_x + 3 * padding, center_y, 0.1)
        ]
        
        # 将每个坦克选项的精灵添加到SpriteList中
        for option in self.tank_options:
            self.tank_sprites.append(option.sprite)
        
        # 默认选中第一个和最后一个坦克(作为初始状态)
        self.player1_selection = self.tank_options[0]
        self.player1_selection.selected = True
        self.player1_selection.player = 1
        
        self.player2_selection = self.tank_options[3]
        self.player2_selection.selected = True
        self.player2_selection.player = 2

    def on_show_view(self):
        """显示视图时的设置"""
        arcade.set_background_color(arcade.color.LIGHT_BLUE)    

    def on_draw(self):
        """绘制视图"""
        self.clear()
        
        # 绘制标题
        arcade.draw_text(
            "选择你的坦克",
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT - 100,
            arcade.color.BLACK,
            font_size=40,
            anchor_x="center"
        )
        # 绘制所有坦克精灵
        self.tank_sprites.draw()
        
        # 绘制每个坦克选项的附加元素 (名称, 选中边框, 玩家标识)
        for option in self.tank_options:
            option.draw()

        # 绘制操作说明
        arcade.draw_text(
            "玩家1使用 A和D 键选择坦克",
            SCREEN_WIDTH / 2,
            150,
            arcade.color.BLACK,
            font_size=18,
            anchor_x="center"
        )
        
        arcade.draw_text(
            "玩家2使用 ← 和 → 键选择坦克",
            SCREEN_WIDTH / 2,
            100,
            arcade.color.BLACK,
            font_size=18,
            anchor_x="center"
        )
        
        # 如果两位玩家都已选择，显示开始游戏提示
        arcade.draw_text(
            "按J开始游戏",
            SCREEN_WIDTH / 2,
            50,
            arcade.color.ORANGE_RED,
            font_size=24,
            anchor_x="center",
            bold=True
        )

    def on_key_press(self, key, modifiers):
        """处理按键事件"""
        # 玩家1的操作
        if key == arcade.key.A:  # 玩家1向左移动选择
            self._move_selection(player=1, direction=-1)
        elif key == arcade.key.D:  # 玩家1向右移动选择
            self._move_selection(player=1, direction=1)
        
        # 玩家2的操作
        elif key == arcade.key.LEFT:  # 玩家2向左移动选择
            self._move_selection(player=2, direction=-1)
        elif key == arcade.key.RIGHT:  # 玩家2向右移动选择
            self._move_selection(player=2, direction=1)
        
        # J键开始游戏
        elif key == arcade.key.J:
            self._start_game()
        
        # 返回上一页
        elif key == arcade.key.ESCAPE:
            from game_views import ModeSelectView
            mode_select_view = ModeSelectView()
            self.window.show_view(mode_select_view)

    def _move_selection(self, player, direction):
        """移动玩家的坦克选择
        
        参数:
            player (int): 玩家编号 (1 或 2)
            direction (int): 移动方向 (-1 向左, 1 向右)
        """
        # 获取当前选择
        current = self.player1_selection if player == 1 else self.player2_selection
        
        # 找到当前选择在列表中的索引
        current_index = self.tank_options.index(current)
        
        # 计算新的索引，并确保在有效范围内
        new_index = (current_index + direction) % len(self.tank_options)
        
        # 检查新选择是否已被另一位玩家选中
        other_selection = self.player2_selection if player == 1 else self.player1_selection
        if self.tank_options[new_index] == other_selection:
            # 如果被另一位玩家选中，再次移动一格
            new_index = (new_index + direction) % len(self.tank_options)
        
        # 更新选择
        if player == 1:
            # 取消当前选择
            self.player1_selection.selected = False
            self.player1_selection.player = None
            # 设置新选择
            self.player1_selection = self.tank_options[new_index]
            self.player1_selection.selected = True
            self.player1_selection.player = 1
        else:
            # 取消当前选择
            self.player2_selection.selected = False
            self.player2_selection.player = None
            # 设置新选择
            self.player2_selection = self.tank_options[new_index]
            self.player2_selection.selected = True
            self.player2_selection.player = 2
        
        

    def _start_game(self):
        """开始游戏，传递选择的坦克"""
        from game_views import GameView
        
        # 创建游戏视图，传入选择的坦克图片路径
        game_view = GameView(
            mode="pvp",
            player1_tank_image=self.player1_selection.image_path,
            player2_tank_image=self.player2_selection.image_path
        )
        
        self.window.show_view(game_view)
