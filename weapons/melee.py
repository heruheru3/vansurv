import pygame
import math
from weapons.base import Weapon  # 相対インポートを絶対インポートに変更
from constants import *
from effects.attack import Attack  # 相対インポートを絶対インポートに変更

class Whip(Weapon):
    def __init__(self):
        super().__init__()
        self.cooldown = 800
        # 近接武器として適切なダメージに調整
        self.damage = 30
        self.range = 200
        # ムチは素早く伸びて消えるイメージにする（短めの持続）
        self.duration = 180
        self.directions = ['right']
        self.last_direction = 'right'
        # 細めのムチにする
        self.width = 12
        self.last_attack_time = 0
        self.is_attacking = False

    def attack(self, player, camera_x=0, camera_y=0):
        current_time = pygame.time.get_ticks()
        
        if not self.can_attack():
            return []
        
        self.update_cooldown()

        # サブアイテム補正を適用
        try:
            range_mult = player.get_effect_range_multiplier()
        except Exception:
            range_mult = 1.0
        try:
            time_mult = player.get_effect_time_multiplier()
        except Exception:
            time_mult = 1.0
        try:
            base_bonus = player.get_base_damage_bonus()
        except Exception:
            base_bonus = 0

        attacks = []
        # プレイヤーの移動方向を取得
        keys = pygame.key.get_pressed()
        moving_left = keys[pygame.K_LEFT]
        moving_right = keys[pygame.K_RIGHT]

        # まずマウスでの移動/ターゲット方向を優先して判定する
        input_direction = None
        try:
            # プレイヤーがマウス制御モードなら target を使う（ただし target は画面座標の場合があるので補正）
            if getattr(player, 'mouse_control', False):
                # プレイヤー.target_* は画面座標で設定されることがあるため、ワールド座標に変換
                tx = getattr(player, 'target_x', player.x)
                ty = getattr(player, 'target_y', player.y)
                try:
                    # 推定: target が画面座標なら camera を加算
                    tx_world = tx + camera_x
                    ty_world = ty + camera_y
                except Exception:
                    tx_world = tx
                    ty_world = ty
                dx = tx_world - player.x
                dy = ty_world - player.y
                dist = math.hypot(dx, dy)
                if dist > getattr(player, 'movement_deadzone', 0):
                    if abs(dx) > abs(dy):
                        input_direction = 'left' if dx < 0 else 'right'
                    else:
                        input_direction = 'up' if dy < 0 else 'down'
            # 左クリックのマウス移動も考慮
            if input_direction is None and pygame.mouse.get_pressed()[0]:
                mx, my = pygame.mouse.get_pos()
                # マウスは画面座標なのでワールド座標に変換
                world_mx = mx + camera_x
                world_my = my + camera_y
                mdx = world_mx - player.x
                mdy = world_my - player.y
                mdist = math.hypot(mdx, mdy)
                if mdist > getattr(player, 'movement_deadzone', 0):
                    if abs(mdx) > abs(mdy):
                        input_direction = 'left' if mdx < 0 else 'right'
                    else:
                        input_direction = 'up' if mdy < 0 else 'down'
        except Exception:
            input_direction = None

        # レベル1の場合、マウス方向（あれば）を優先、なければキーボード移動または最後の方向を使用
        if self.level == 1:
            if input_direction:
                self.last_direction = input_direction
                self.directions = [input_direction]
            elif moving_left:
                self.last_direction = 'left'
                self.directions = ['left']
            elif moving_right:
                self.last_direction = 'right'
                self.directions = ['right']
            else:
                self.directions = [self.last_direction]

        # サブアイテムのレンジ/時間/ダメージ補正を反映した値を計算
        effective_range = max(1, int(self.range * range_mult))
        effective_duration = int(self.duration * time_mult)
        effective_damage = self.damage + base_bonus

        # 攻撃を生成
        for direction in self.directions:
            if direction == 'up':
                x = player.x
                y = player.y - effective_range/2
                width = self.width
                height = effective_range
            elif direction == 'down':
                x = player.x
                y = player.y + effective_range/2
                width = self.width
                height = effective_range
            elif direction == 'left':
                x = player.x - effective_range/2
                y = player.y
                width = effective_range
                height = self.width
            elif direction == 'right':
                x = player.x + effective_range/2
                y = player.y
                width = effective_range
                height = self.width

            attacks.append(
                Attack(
                    x=x,
                    y=y,
                    size_x=width,
                    size_y=height,
                    type_="whip",
                    duration=effective_duration,
                    direction=direction,
                    follow_player=player,
                    damage=effective_damage
                )
            )
            # 生成したAttackにムチ用パラメータを付与（描画・アニメ用）
            atk = attacks[-1]
            atk.length = effective_range  # ムチの長さ
            atk.width = self.width   # 描画幅（細め）
            atk.direction = direction
        
        return attacks

    def level_up(self):
        """レベルに応じて攻撃方向を設定"""
        if self.level == 1:
            # レベル1は現在の方向を維持
            pass
        elif self.level == 2:
            self.directions = ['left', 'right']  # 左右両方
        elif self.level == 3:
            self.directions = ['left', 'right', 'up']  # 左右上
        elif self.level == 4:
            self.directions = ['left', 'right', 'up', 'down']  # 全方向
        
        # レベルアップ時の強化
        self.range *= 1.1  # 範囲10%増加
        self.width = int(self.width * 1.1)  # 攻撃の太さも10%増加

class Garlic(Weapon):
    def __init__(self):
        super().__init__()
        self.cooldown = 1000
        # 持続系なので1回あたりのダメージは小さめに設定
        self.damage = 5
        self.radius = 80
        self.duration = 1000

    def attack(self, player):
        if not self.can_attack():
            return []

        self.update_cooldown()

        # サブアイテムの補正を適用
        try:
            range_mult = player.get_effect_range_multiplier()
        except Exception:
            range_mult = 1.0
        try:
            time_mult = player.get_effect_time_multiplier()
        except Exception:
            time_mult = 1.0
        try:
            base_bonus = player.get_base_damage_bonus()
        except Exception:
            base_bonus = 0

        effective_radius = max(1, int(self.radius * range_mult))
        effective_duration = int(self.duration * time_mult)
        effective_damage = self.damage + base_bonus

        return [Attack(x=player.x,
                      y=player.y,
                      size_x=effective_radius * 2,  # 直径を指定
                      size_y=effective_radius * 2,
                      type_="garlic",
                      duration=effective_duration,
                      follow_player=player,
                      damage=effective_damage)]

    def level_up(self):
        """レベルアップ時の強化"""
        super().level_up()
        self.radius = int(self.radius * 1.1)  # 範囲10%増加
        self.damage *= 1.2  # ダメージ20%増加