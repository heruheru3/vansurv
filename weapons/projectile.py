import pygame
import math
import random
from .base import Weapon
from constants import *  # 相対インポートを絶対インポートに変更
from effects.attack import Attack

class HolyWater(Weapon):
    def __init__(self):
        super().__init__()
        self.cooldown = 2000
        # 範囲攻撃のためやや低めに設定
        self.damage = 8
        self.duration = 1000
        self.radius = 50  # 初期範囲を50に設定
        self.num_attacks = 1  # 初期の攻撃個数

    def attack(self, player):
        if not self.can_attack():
            return []
        
        self.update_cooldown()
        attacks = []
        
        # サブアイテムによる補正を適用
        try:
            range_mult = player.get_effect_range_multiplier()
        except Exception:
            range_mult = 1.0
        try:
            time_mult = player.get_effect_time_multiplier()
        except Exception:
            time_mult = 1.0
        try:
            extra = player.get_extra_projectiles()
        except Exception:
            extra = 0
        try:
            base_mult = player.get_base_damage_bonus()
        except Exception:
            base_mult = 1.0

        effective_radius = max(1, int(self.radius * range_mult))
        effective_duration = int(self.duration * time_mult)
        effective_damage = self.damage * base_mult
        effective_count = max(1, int(self.num_attacks + extra))
        
        # レベルに応じた攻撃数で生成
        # 複数発生する場合は短い遅延を挟んで順次発生させる
        delay_step = 120  # ms の単位で短い遅延
        for i in range(effective_count):
            x = player.x + random.randint(-150, 150)  # 散布範囲を広げる
            y = player.y + random.randint(-150, 150)
            atk = Attack(x=x,
                         y=y,
                         size_x=effective_radius * 2,  # 直径を指定
                         size_y=effective_radius * 2,
                         type_="holy_water",
                         duration=effective_duration,
                         damage=effective_damage)
            # 複数個の場合は順次スポーンさせるため spawn_delay を設定
            try:
                if effective_count > 1:
                    atk.spawn_delay = int(i * delay_step)
                    atk._pending = True
            except Exception:
                pass
            attacks.append(atk)
        
        return attacks

    def level_up(self):
        """レベルアップ時の強化"""
        super().level_up()
        if self.level % 2 == 0:  # 偶数レベルで攻撃範囲増加
            self.radius = int(self.radius * 1.2)  # 範囲20%増加
        else:  # 奇数レベルで攻撃個数増加
            self.num_attacks += 1  # 攻撃個数+1
        self.damage *= 1.1  # ダメージ10%増加

class MagicWand(Weapon):
    def __init__(self):
        super().__init__()
        self.cooldown = 1000
        # 追尾弾は単発でそこそこのダメージ
        self.damage = 12
        self.speed = 5
        self.num_projectiles = 1

    def attack(self, player, enemies):
        if not self.can_attack() or not enemies:
            return []
        
        self.update_cooldown()
        attacks = []

        # サブアイテム補正
        try:
            extra = player.get_extra_projectiles()
        except Exception:
            extra = 0
        try:
            base_mult = player.get_base_damage_bonus()
        except Exception:
            base_mult = 1.0
        try:
            proj_speed_mult = player.get_projectile_speed()
        except Exception:
            proj_speed_mult = 1.0

        effective_num = max(1, int(self.num_projectiles + extra))
        effective_damage = self.damage * base_mult
        effective_speed = self.speed * proj_speed_mult
        
        # プレイヤーに最も近い順にnum_projectiles分の敵をターゲット
        sorted_enemies = sorted(enemies, 
                              key=lambda e: math.sqrt((e.x - player.x)**2 + (e.y - player.y)**2))
        targets = sorted_enemies[:effective_num]
        
        for target in targets:
            attacks.append(
                Attack(x=player.x, 
                      y=player.y, 
                      size_x=10, 
                      size_y=10, 
                      type_="magic_wand", 
                      target=target, 
                      speed=effective_speed,
                      damage=effective_damage)
            )
        
        return attacks

    def level_up(self):
        """レベルアップ時の強化"""
        if self.level % 2 == 0:  # 現在のレベルが偶数（次は奇数に）
            self.speed += 2
            print(f"Speed increased to {self.speed}")
        else:  # 現在のレベルが奇数（次は偶数に）
            self.num_projectiles += 1
            print(f"Projectiles increased to {self.num_projectiles}")
            
        # 基本強化（レベルを上げる前に効果を適用）
        self.damage *= 1.1  # ダメージ10%増加
        self.num_projectiles += 1
        self.cooldown = max(self.cooldown * 0.95, 500)  # クールダウン短縮（最小500ms）
        
        # 最後にレベルを上げる
        super().level_up()

class Axe(Weapon):
    def __init__(self):
        super().__init__()
        self.cooldown = 1000
        # 投擲武器: 中程度のダメージ
        self.damage = 25
        self.size = 50  # 攻撃範囲
        self.throw_speed = 6  # 投げる速度
        self.rotation_speed = 0.3  # 回転速度

    def attack(self, player):
        if not self.can_attack():
            return []

        self.update_cooldown()
        # サブアイテム補正を取得
        try:
            proj_speed_mult = player.get_projectile_speed()
        except Exception:
            proj_speed_mult = 1.0
        try:
            base_mult = player.get_base_damage_bonus()
        except Exception:
            base_mult = 1.0
        try:
            range_mult = player.get_effect_range_multiplier()
        except Exception:
            range_mult = 1.0
        try:
            time_mult = player.get_effect_time_multiplier()
        except Exception:
            time_mult = 1.0
        try:
            extra = player.get_extra_projectiles()
        except Exception:
            extra = 0

        effective_size = max(1, int(self.size * range_mult))
        effective_duration = max(100, int(3000 * time_mult))
        effective_damage = self.damage * base_mult
        effective_num = max(1, int(1 + extra))
        
        attacks = []
        for i in range(effective_num):
            # ランダムな角度で発射（複数投擲時は若干の分散を持たせる）
            angle = math.radians(random.uniform(0, 360))
            # 基本速度にプロジェクタイル速度補正を反映
            vx = math.cos(angle) * (self.throw_speed * proj_speed_mult)
            vy = math.sin(angle) * (self.throw_speed * proj_speed_mult)
            eff_speed = self.throw_speed * proj_speed_mult

            attacks.append(Attack(x=player.x,
                                  y=player.y,
                                  size_x=effective_size,
                                  size_y=effective_size,
                                  type_="axe",
                                  duration=effective_duration,
                                  speed=eff_speed,
                                  velocity_x=vx,
                                  velocity_y=vy,
                                  rotation_speed=self.rotation_speed,
                                  damage=effective_damage))
        
        return attacks

    def level_up(self):
        """レベルアップ時の強化"""
        super().level_up()
        self.size = int(self.size * 1.3)  # 範囲20%増加
        self.throw_speed += 1  # 投げる速度増加
        self.damage *= 1.2  # ダメージ15%増加
        self.cooldown = max(self.cooldown * 0.95, 800)  # クールダウン減少（最小800ms）

class Stone(Weapon):
    def __init__(self):
        super().__init__()
        self.cooldown = 1500
        # 貫通・バウンドするため中程度
        self.damage = 15
        self.speed = 15
        self.bounces = 2
        self.duration = 5000
        self.size = 25  # サイズ属性を追加

    def attack(self, player):
        if not self.can_attack():
            return []
        
        self.update_cooldown()
        # ランダムな角度（0-360度）を生成
        angle = math.radians(random.uniform(0, 360))
        
        try:
            mult = player.get_projectile_speed()
        except Exception:
            mult = 1.0
        spd = self.speed * mult

        try:
            base_mult = player.get_base_damage_bonus()
        except Exception:
            base_mult = 1.0
        
        return [Attack(
            x=player.x, 
            y=player.y, 
            size_x=self.size,  # self.sizeを使用
            size_y=self.size,  # self.sizeを使用
            type_="stone",
            speed=spd,
            duration=self.duration,
            bounces=self.bounces,
            velocity_x=math.cos(angle) * spd,
            velocity_y=math.sin(angle) * spd,
            damage=self.damage * base_mult
        )]

    def level_up(self):
        """レベルアップ時の強化"""
        super().level_up()
        self.speed *= 1.3       # 速度増加
        self.bounces += 1    # バウンド回数増加
        self.damage *= 1.3  # ダメージ30%増加
        self.size += 2       # サイズ増加

class RotatingBook(Weapon):
    """プレイヤーの周りを回転する本（フォローしつつ回転）"""
    def __init__(self):
        super().__init__()
        self.cooldown = 6000
        self.damage = 15
        self.orbit_radius = 80
        # 回転速度は個別に保持し、レベルアップで変化させる
        self.rotation_speed = 0.05
        self.num_books = 1
        self.duration = 5000
        # 本の描画サイズ（幅・高さ）をプロパティ化してレベルアップで拡大可能にする
        self.book_w = 24
        self.book_h = 16

    def attack(self, player):
        if not self.can_attack():
            return []
        self.update_cooldown()
        attacks = []

        try:
            range_mult = player.get_effect_range_multiplier()
        except Exception:
            range_mult = 1.0
        try:
            time_mult = player.get_effect_time_multiplier()
        except Exception:
            time_mult = 1.0
        try:
            extra = player.get_extra_projectiles()
        except Exception:
            extra = 0
        try:
            base_bonus = player.get_base_damage_bonus()
        except Exception:
            base_bonus = 0

        effective_radius = max(1, int(self.orbit_radius * range_mult))
        effective_duration = int(self.duration * time_mult)
        effective_books = max(1, int(self.num_books + extra))
        effective_damage = self.damage + base_bonus

        for i in range(effective_books):
            angle = (2 * math.pi * i) / max(1, effective_books)
            a = Attack(x=player.x + math.cos(angle) * effective_radius,
                       y=player.y + math.sin(angle) * effective_radius,
                       # 本のサイズはプロパティから取得する
                       size_x=int(self.book_w * range_mult),
                       size_y=int(self.book_h * range_mult),
                       type_="book",
                       duration=effective_duration,
                       follow_player=player,
                       damage=effective_damage)
            # 回転用パラメータ
            a.orbit_radius = effective_radius
            a.orbit_angle = angle
            # Attack に回転速度を反映
            a.rotation_speed = self.rotation_speed
            attacks.append(a)
        return attacks

    def level_up(self):
        super().level_up()
        # レベルに応じて本の数や半径を増やす
        # if self.level % 2 == 0:
        self.num_books += 1
        self.orbit_radius = int(self.orbit_radius * 1.05)
        self.damage = int(self.damage * 1.15)
        self.cooldown = min(int(self.cooldown * 0.95), 5000)
        # 本のサイズと回転速度も強化して、視覚的に派手にする
        try:
            self.book_w = min(60, int(self.book_w * 1.2))
            self.book_h = min(40, int(self.book_h * 1.2))
            # 回転速度は積算的に高める（一定の上限を設ける）
            self.rotation_speed = min(1.5, self.rotation_speed * 1.15)
        except Exception:
            pass

class Knife(Weapon):
    """プレイヤーの向いている方向へ直線で投擲するナイフ

    複数本同時に射出できるようにし、各弾は発射方向に対して平行に並んだ配置で生成される。
    """
    def __init__(self):
        super().__init__()
        self.cooldown = 500
        self.damage = 18
        self.speed = 12
        self.size = 10
        # 追加: 発射本数と本数間の間隔（ピクセル）
        self.num_knives = 1
        self.spacing = 15

    def attack(self, player, camera_x=0, camera_y=0):
        if not self.can_attack():
            return []
        self.update_cooldown()

        # 角度はマウス位置優先、なければ移動方向
        angle = None
        try:
            mx, my = pygame.mouse.get_pos()
            world_mx = mx + camera_x
            world_my = my + camera_y
            dx = world_mx - player.x
            dy = world_my - player.y
            if dx == 0 and dy == 0:
                angle = None
            else:
                angle = math.atan2(dy, dx)
        except Exception:
            angle = None

        if angle is None:
            # プレイヤーの向きが取れるならそれを使う
            angle = 0
            try:
                ld = getattr(player, 'last_direction', 'right')
                lookup = {'right': 0.0, 'left': math.pi, 'up': -math.pi/2, 'down': math.pi/2}
                angle = lookup.get(ld, 0.0)
            except Exception:
                angle = 0

        # apply projectile speed multiplier
        try:
            mult = player.get_projectile_speed()
        except Exception:
            mult = 1.0

        vx = math.cos(angle) * (self.speed * mult)
        vy = math.sin(angle) * (self.speed * mult)

        attacks = []
        # 発射方向に対して並列に（平行に）並べるため、法線ベクトルを使って生成位置をオフセット
        perp_x = -math.sin(angle)
        perp_y = math.cos(angle)

        # 中心から左右に広がるようにオフセットを計算
        # 例: num_knives=3 -> offsets = [-1, 0, 1] * spacing
        try:
            extra = player.get_extra_projectiles()
        except Exception:
            extra = 0
        effective_knives = max(1, int(self.num_knives + extra))
        mid = (effective_knives - 1) / 2.0
        # 発射遅延（ms）: 中央は0、周辺ほど遅らせる
        delay_step = 100
        for i in range(effective_knives):
            offset = (i - mid) * self.spacing
            sx = player.x + perp_x * offset
            sy = player.y + perp_y * offset

            atk = Attack(x=sx,
                         y=sy,
                         size_x=self.size,
                         size_y=self.size,
                         type_="knife",
                         duration=1500,
                         velocity_x=vx,
                         velocity_y=vy,
                         damage=self.damage)
            # 追加: 中央からの距離に応じて発射を遅延させる
            try:
                import math as _math
                delay_index = int(_math.ceil(abs(i - mid)))
                if delay_index > 0:
                    atk.spawn_delay = delay_index * delay_step
                    atk._pending = True
            except Exception:
                pass
            attacks.append(atk)

        return attacks

    def level_up(self):
        # レベルが上がるごとに本数を1本増やす（上限を設定して暴発を防止）
        super().level_up()
        self.num_knives = min(8, self.num_knives + 1)  # 上限は8本に設定
        # 既存の強化処理
        try:
            self.speed = int(self.speed * 1.1)
            self.damage = int(self.damage * 1.15)
            self.cooldown = max(int(self.cooldown * 0.95), 120)
        except Exception:
            pass

class Thunder(Weapon):
    """ランダム地点にエネミーの上空から攻撃を行うサンダー"""
    def __init__(self):
        super().__init__()
        self.cooldown = 2000
        self.damage = 40
        self.num_strikes = 1
        self.duration = 500
        self.height_offset = 120
        self.area_size = 60

    def attack(self, player, enemies=None, camera_x=0, camera_y=0):
        if not self.can_attack():
            return []
        self.update_cooldown()
        attacks = []
        targets = []

        try:
            extra = player.get_extra_projectiles()
        except Exception:
            extra = 0
        try:
            range_mult = player.get_effect_range_multiplier()
        except Exception:
            range_mult = 1.0
        try:
            base_bonus = player.get_base_damage_bonus()
        except Exception:
            base_bonus = 0

        effective_area = max(8, int(self.area_size * range_mult))
        effective_num = max(1, int(self.num_strikes + extra))
        effective_damage = self.damage + base_bonus

        if enemies:
            # 画面内の敵（カメラ範囲内）を優先してターゲットする
            try:
                visible = [e for e in enemies if (camera_x is None or camera_y is None) or (camera_x <= e.x <= camera_x + SCREEN_WIDTH and camera_y <= e.y <= camera_y + SCREEN_HEIGHT)]
            except Exception:
                visible = []
            pool = visible if visible else enemies
            k = min(len(pool), max(1, effective_num))
            try:
                targets = random.sample(pool, k)
            except Exception:
                targets = pool[:k]
        else:
            targets = []

        # 複数のターゲットに対して順次発生させるため遅延を設定
        delay_step = 120
        for i, t in enumerate(targets):
            # 上空から落ちるエフェクト: 目標位置を敵の頭上に設定
            try:
                target_x = t.x
                # 敵のサイズがある場合は頭上に少しオフセット
                head_offset = getattr(t, 'size', 0)
                head_offset_val = max(0, int(head_offset * 0.9)) + 4
                head_y = t.y - head_offset_val
            except Exception:
                target_x = t.x
                head_y = t.y
                head_offset_val = 0

            atk = Attack(x=target_x,
                         y=head_y,
                         size_x=effective_area,
                         size_y=effective_area,
                         type_="thunder",
                         duration=self.duration,
                         damage=effective_damage)
            # 目標の参照と頭上オフセットを保持（敵が移動しても追従させるため）
            try:
                atk.target = t
                atk.head_offset = head_offset_val
            except Exception:
                pass
            # 落下開始位置は頭上よりさらに上に設定して上空から落ちてくる表現にする
            atk.strike_from_y = head_y - self.height_offset
            try:
                if effective_num > 1:
                    atk.spawn_delay = int(i * delay_step)
                    atk._pending = True
            except Exception:
                pass
            attacks.append(atk)

        # 敵がいない場合はプレイヤー周辺のランダム地点に落とす
        if not targets:
            delay_step = 120
            for i in range(effective_num):
                rx = player.x + random.randint(-200, 200)
                ry = player.y + random.randint(-200, 200)
                atk = Attack(x=rx, y=ry, size_x=effective_area, size_y=effective_area, type_="thunder", duration=self.duration, damage=effective_damage)
                atk.strike_from_y = ry - self.height_offset
                try:
                    if effective_num > 1:
                        atk.spawn_delay = int(i * delay_step)
                        atk._pending = True
                except Exception:
                    pass
                attacks.append(atk)

        return attacks

    def level_up(self):
        super().level_up()
        self.num_strikes = min(4, self.num_strikes + 1)
        self.damage = int(self.damage * 1.15)
        self.cooldown = max(int(self.cooldown * 0.9), 500)