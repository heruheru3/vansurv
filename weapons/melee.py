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

    def attack(self, player, camera_x=0, camera_y=0, get_virtual_mouse_pos=None):
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
                if get_virtual_mouse_pos:
                    # 仮想マウス座標を使用
                    mx, my = get_virtual_mouse_pos()
                else:
                    # 従来の方法（後方互換性のため）
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
        # 発射方向を決定: 入力（マウス/キー）を優先、なければ last_direction を使用
        primary_dir = None
        if input_direction in ('left', 'right'):
            primary_dir = input_direction
            self.last_direction = primary_dir
        elif moving_left:
            primary_dir = 'left'
            self.last_direction = 'left'
        elif moving_right:
            primary_dir = 'right'
            self.last_direction = 'right'
        else:
            primary_dir = self.last_direction or 'right'

        # レベルに応じて単発/両方向を切り替え
        if self.level <= 2:
            use_dirs = [primary_dir]
        else:
            # レベル3以上は前方と後方（左右反転）の両方。後方は遅延発生させる
            opposite = 'left' if primary_dir == 'right' else 'right'
            use_dirs = [primary_dir, opposite]

        # サブアイテムのレンジ/時間/ダメージ補正を反映した値を計算
        effective_range = max(1, int(self.range * range_mult))
        effective_duration = int(self.duration * time_mult)
        effective_damage = self.damage + base_bonus

        # 攻撃を生成
        for i, direction in enumerate(use_dirs):
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
            # レベル3以上で2つ目（後方）のムチは少し遅延して発生させる
            if self.level >= 3 and i == 1:
                try:
                    delay_ms = max(40, int(self.duration * 0.4))  # 適度な遅延
                    atk.spawn_delay = delay_ms
                    atk._pending = True
                except Exception:
                    pass

        return attacks

    def level_up(self):
        """レベルに応じて攻撃方向を設定"""
        # 基底の level_up を呼んで level を増やす
        super().level_up()
        # 方向は attack() 側で動的に決定する（レベルにより単発/両方向を切替）

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

        # ガーリックの当たり判定を適切に設定
        # Attack内で // 2 される分を考慮して、実際の効果範囲の2倍で設定
        garlic_size = effective_radius * 2

        return [Attack(x=player.x,
                      y=player.y,
                      size_x=garlic_size,  # 当たり判定を適切に設定
                      size_y=garlic_size,
                      type_="garlic",
                      duration=effective_duration,
                      follow_player=player,
                      damage=effective_damage)]

    def level_up(self):
        """レベルアップ時の強化"""
        super().level_up()
        self.radius = int(self.radius * 1.2)  # 範囲20%増加
        self.damage *= 1.3  # ダメージ30%増加