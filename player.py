import pygame
import math
import random
import os
import sys
from constants import *
from weapons.melee import Whip, Garlic
from weapons.projectile import HolyWater, MagicWand, Axe, Stone, RotatingBook, Knife, Thunder
from subitems import get_default_subitems, random_upgrade

def resource_path(relative_path):
    """PyInstallerで実行時にリソースファイルの正しいパスを取得する"""
    try:
        # PyInstallerで実行されている場合
        base_path = sys._MEIPASS
    except Exception:
        # 通常のPythonで実行されている場合
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class Player:
    def __init__(self, screen):
        self.screen = screen
        # 位置・移動（初期位置は後で安全な場所に調整）
        self.x = WORLD_WIDTH // 2
        self.y = WORLD_HEIGHT // 2
        # self.speed = 3
        self.base_speed = 2.5
        self.size = 24
        
        # 安全な開始位置を見つける
        self._adjust_spawn_position()
        
        # 基本ステータス
        self.max_hp = 100
        self.hp = self.max_hp
        self.defense = 1
        self.avoidance = 0.1
        self.exp = 0
        self.level = 1
        self.exp_to_next_level = 3

        # 武器定義
        all_weapons = {
            'whip': Whip,
            'holy_water': HolyWater,
            'garlic': Garlic,
            'magic_wand': MagicWand,
            'axe': Axe,
            'stone': Stone,
            'rotating_book': RotatingBook,
            'knife': Knife,
            'thunder': Thunder,
        }
        self.weapons = {}
        self.available_weapons = all_weapons.copy()
        self.active_attacks = []

        # 入力・移動補助
        self.target_x = self.x
        self.target_y = self.y
        self.mouse_control = False
        self.movement_deadzone = 10
        self.mouse_speed_multiplier = 1.0
        self.mouse_distance_scaling = False
        self.vx = 0.0
        self.vy = 0.0

        # 移動方向の記録（武器の発射方向に使用）
        self.last_direction = 'right'
        self.movement_dx = 0.0
        self.movement_dy = 0.0
        self.last_attack_angle = 0.0  # 最後の発射角度を記録

        # マグネット効果
        self.magnet_active = False
        self.magnet_end_time = 0
        # gem_pickup_range取得によるmagnetの出現率倍率（初期値は1.0 = 100%）
        self.magnet_drop_rate_multiplier = 1.0

        # 画面揺れエフェクト
        self.screen_shake_active = False
        self.screen_shake_end_time = 0
        self.screen_shake_intensity = 0

        # UI制御
        self.last_input_method = "keyboard"  # "keyboard" or "mouse"
        self.show_keyboard_cursor = True

        # 見た目（オーブ + スプライト）
        orb_size = max(32, self.size * 3)
        self.orb_base = pygame.Surface((orb_size, orb_size), pygame.SRCALPHA)
        cx, cy = orb_size // 2, orb_size // 2
        for i in range(orb_size // 2, 0, -1):
            t = i / (orb_size // 2)
            glow_col = (30 + int(50 * t), 140 + int(80 * t), 80 + int(80 * t), int(20 * t))
            pygame.draw.circle(self.orb_base, glow_col, (cx, cy), i)
        band_rect = (0, int(orb_size * 0.42), orb_size, int(orb_size * 0.16))
        pygame.draw.ellipse(self.orb_base, (20, 90, 60, 180), band_rect)
        mark_count = 10
        for m in range(mark_count):
            ang = (2 * math.pi * m) / mark_count
            mx = cx + int(math.cos(ang) * orb_size * 0.38)
            my = cy + int(math.sin(ang) * orb_size * 0.02)
            pygame.draw.circle(self.orb_base, (40, 130, 90, 220), (mx, my), max(1, orb_size // 20))
        self.orb_angle = 0.0
        self.prev_x = float(self.x)
        self.prev_y = float(self.y)
        self.distance_traveled = 0.0

        # スプライト
        try:
            chip_path = resource_path(os.path.join('assets', 'character', 'player_chip.png'))
            sheet = pygame.image.load(chip_path).convert_alpha()
            sheet_w = sheet.get_width()
            sheet_h = sheet.get_height()
            tile_w = 16
            self.frames = []
            for x in range(0, min(sheet_w, 64), tile_w):
                frame = sheet.subsurface((x, 0, tile_w, sheet_h)).copy()
                self.frames.append(frame)
            if not self.frames:
                raise Exception('no frames')
        except Exception:
            self.frames = []

        self.frame_index = 0
        self.anim_tick = 0
        self.anim_speed = 6
        self.facing = 'left'

        # フラグ・サブアイテム
        self.auto_heal_on_level_up = False
        self.natural_regen_base = 0
        self.last_regen_ms = pygame.time.get_ticks()
        try:
            self.subitem_templates = get_default_subitems()
        except Exception:
            self.subitem_templates = {}
        self.subitems = {}

        # レベルアップUI状態
        self.last_level_choices = []
        self.awaiting_weapon_choice = False
        self.last_subitem_choices = []
        self.awaiting_subitem_choice = False
        self.selected_weapon_choice_index = 0
        self.selected_subitem_choice_index = 0

        try:
            self.upgrade_weapons()
        except Exception:
            pass

    def move(self, camera_x=0, camera_y=0, get_virtual_mouse_pos=None):
        dx = 0.0
        dy = 0.0
        keys = pygame.key.get_pressed()
        
        # キーボード入力の記録
        keyboard_input = False
        if keys[pygame.K_LEFT]:
            dx -= 1.0
            keyboard_input = True
        if keys[pygame.K_RIGHT]:
            dx += 1.0
            keyboard_input = True
        if keys[pygame.K_UP]:
            dy -= 1.0
            keyboard_input = True
        if keys[pygame.K_DOWN]:
            dy += 1.0
            keyboard_input = True

        # キーボード入力がある場合は移動方向を記録
        if keyboard_input:
            if dx != 0 or dy != 0:
                # 移動方向を正規化して記録
                length = math.hypot(dx, dy)
                if length > 0:
                    self.movement_dx = dx / length
                    self.movement_dy = dy / length
                    
                    # 主要な方向を決定
                    if abs(dx) > abs(dy):
                        if dx > 0:
                            self.last_direction = 'right'
                        else:
                            self.last_direction = 'left'
                    else:
                        if dy > 0:
                            self.last_direction = 'down'
                        else:
                            self.last_direction = 'up'
        else:
            # キーボード入力がない場合（静止状態）は移動ベクトルをクリア
            self.movement_dx = 0.0
            self.movement_dy = 0.0

        if pygame.mouse.get_pressed()[0]:
            if get_virtual_mouse_pos:
                # 仮想マウス座標を使用
                mouse_x, mouse_y = get_virtual_mouse_pos()
            else:
                # 従来の方法（後方互換性のため）
                mouse_x, mouse_y = pygame.mouse.get_pos()
            world_mouse_x = mouse_x + camera_x
            world_mouse_y = mouse_y + camera_y
            mouse_dx = world_mouse_x - self.x
            mouse_dy = world_mouse_y - self.y
            distance = math.hypot(mouse_dx, mouse_dy)
            if distance > self.movement_deadzone:
                dir_x = mouse_dx / distance
                dir_y = mouse_dy / distance
                dx += dir_x * self.mouse_speed_multiplier
                dy += dir_y * self.mouse_speed_multiplier

        length = math.hypot(dx, dy)
        sp = self.get_speed()
        if length > 0:
            nx = dx / length
            ny = dy / length
            
            # 新しい位置を計算
            new_x = self.x + nx * sp
            new_y = self.y + ny * sp
            
            # 障害物との衝突判定（マップが有効な場合のみ）
            if USE_CSV_MAP:
                try:
                    from stage import get_stage_map
                    stage_map = get_stage_map()
                    
                    # プレイヤーの四隅をチェック
                    corners = [
                        (new_x - self.size//2, new_y - self.size//2),  # 左上
                        (new_x + self.size//2, new_y - self.size//2),  # 右上
                        (new_x - self.size//2, new_y + self.size//2),  # 左下
                        (new_x + self.size//2, new_y + self.size//2),  # 右下
                    ]
                    
                    # X軸方向の移動をチェック
                    x_blocked = False
                    test_x = self.x + nx * sp
                    for corner_x, corner_y in [(test_x - self.size//2, self.y - self.size//2), 
                                               (test_x + self.size//2, self.y - self.size//2),
                                               (test_x - self.size//2, self.y + self.size//2),
                                               (test_x + self.size//2, self.y + self.size//2)]:
                        if stage_map.is_obstacle_at_world_pos(corner_x, corner_y):
                            x_blocked = True
                            break
                    
                    # Y軸方向の移動をチェック
                    y_blocked = False
                    test_y = self.y + ny * sp
                    for corner_x, corner_y in [(self.x - self.size//2, test_y - self.size//2),
                                               (self.x + self.size//2, test_y - self.size//2),
                                               (self.x - self.size//2, test_y + self.size//2),
                                               (self.x + self.size//2, test_y + self.size//2)]:
                        if stage_map.is_obstacle_at_world_pos(corner_x, corner_y):
                            y_blocked = True
                            break
                    
                    # 移動を適用
                    if not x_blocked:
                        self.x = test_x
                    if not y_blocked:
                        self.y = test_y
                        
                except Exception:
                    # 障害物判定に失敗した場合は通常の移動
                    self.x = new_x
                    self.y = new_y
            else:
                # マップが無効な場合は障害物判定なしで移動
                self.x = new_x
                self.y = new_y
            
            self.vx = nx * sp
            self.vy = ny * sp
        else:
            self.vx = 0.0
            self.vy = 0.0

        self.x = max(self.size, min(self.x, WORLD_WIDTH - self.size))
        self.y = max(self.size, min(self.y, WORLD_HEIGHT - self.size))

        dxp = self.x - self.prev_x
        dyp = self.y - self.prev_y
        moved = math.hypot(dxp, dyp)
        if moved > 0:
            self.distance_traveled += moved
        self.prev_x = float(self.x)
        self.prev_y = float(self.y)

    def update_attacks(self, enemies, camera_x=None, camera_y=None, get_virtual_mouse_pos=None):
        self.active_attacks = [a for a in self.active_attacks if not a.is_expired()]
        import inspect
        for weapon_name, weapon in self.weapons.items():
            new_attacks = []
            atk_fn = getattr(weapon, 'attack', None)
            if not atk_fn:
                continue
            try:
                sig = inspect.signature(atk_fn)
                params = list(sig.parameters.keys())
            except Exception:
                params = []
            try:
                if 'enemies' in params:
                    try:
                        new_attacks = atk_fn(self, enemies, camera_x=camera_x, camera_y=camera_y, get_virtual_mouse_pos=get_virtual_mouse_pos)
                    except TypeError:
                        try:
                            new_attacks = atk_fn(self, enemies, camera_x=camera_x, camera_y=camera_y)
                        except TypeError:
                            new_attacks = atk_fn(self, enemies)
                else:
                    if 'camera_x' in params or 'camera_y' in params:
                        try:
                            new_attacks = atk_fn(self, camera_x=camera_x, camera_y=camera_y, get_virtual_mouse_pos=get_virtual_mouse_pos)
                        except TypeError:
                            new_attacks = atk_fn(self, camera_x=camera_x, camera_y=camera_y)
                    else:
                        new_attacks = atk_fn(self)
            except Exception:
                new_attacks = []
            if new_attacks:
                self.active_attacks.extend(new_attacks)

        for attack in self.active_attacks:
            try:
                attack.update(camera_x, camera_y)
            except TypeError:
                attack.update()

    def draw(self, screen, camera_x=0, camera_y=0):
        sx = int(self.x - camera_x)
        sy = int(self.y - camera_y)

        r = self.size
        shadow_w, shadow_h = int(r * 2), int(max(1, r * 0.9))
        shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 120), (0, 0, shadow_w, shadow_h))
        shadow_rect = shadow_surf.get_rect(center=(int(sx), int(sy + r * 1.0)))
        screen.blit(shadow_surf, shadow_rect.topleft)

        if self.vx < -0.1:
            self.facing = 'left'
        elif self.vx > 0.1:
            self.facing = 'right'

        moving = math.hypot(self.vx, self.vy) > 0.1
        if self.frames:
            if moving:
                self.anim_tick += 1
                if self.anim_tick >= self.anim_speed:
                    self.anim_tick = 0
                    self.frame_index = (self.frame_index + 1) % len(self.frames)
            else:
                self.frame_index = 0
                self.anim_tick = 0

            frame = self.frames[self.frame_index]
            target_size = (int(r * 2), int(r * 2))
            frame_s = pygame.transform.scale(frame, target_size)
            if self.facing == 'right':
                frame_s = pygame.transform.flip(frame_s, True, False)
            screen.blit(frame_s, (int(sx - r), int(sy - r)))

            hl_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(hl_surf, (220, 250, 220, 12), (r, r), max(1, r // 3))
            hx = int(sx - (self.vx * 2.5))
            hy = int(sy - (self.vy * 2.5) - r * 0.12)
            screen.blit(hl_surf, (hx - r, hy - r))
        else:
            surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            base = (50, 200, 80)
            darker = tuple(max(0, int(c * 0.45)) for c in base)
            for i in range(r, 0, -1):
                t = i / r
                col = tuple(int(darker[j] + (base[j] - darker[j]) * t) for j in range(3))
                alpha = int(100 * (0.4 + 0.6 * t))
                pygame.draw.circle(surf, col + (alpha,), (r, r), i)
            pygame.draw.circle(surf, (0, 0, 0, 100), (r, r), r, 1)
            screen.blit(surf, (int(sx - r), int(sy - r)))

            orb_w = self.orb_base.get_width()
            radius = max(1.0, orb_w / 2.0)
            angle_deg = math.degrees(self.distance_traveled / radius)
            if abs(self.vx) >= abs(self.vy):
                sign = -math.copysign(1.0, self.vx) if self.vx != 0 else 1.0
            else:
                sign = -math.copysign(1.0, self.vy) if self.vy != 0 else 1.0
            draw_angle = (angle_deg * sign + self.orb_angle) % 360.0
            rotated = pygame.transform.rotate(self.orb_base, draw_angle)
            rr = rotated.get_rect(center=(int(sx), int(sy)))
            screen.blit(rotated, rr.topleft)

            hx = int(sx - (self.vx * 2.5))
            hy = int(sy - (self.vy * 2.5) - r * 0.12)
            hl_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(hl_surf, (220, 250, 220, 18), (r, r), max(1, r // 3))
            screen.blit(hl_surf, (hx - r, hy - r))

            if self.distance_traveled > radius * math.pi * 2:
                self.distance_traveled %= (radius * math.pi * 2)

    def draw_attacks(self, screen, camera_x=0, camera_y=0):
        for attack in self.active_attacks:
            try:
                attack.draw(screen, camera_x, camera_y)
            except TypeError:
                attack.draw(screen)

    def add_exp(self, amount):
        self.exp += amount
        if self.exp >= self.exp_to_next_level:
            self.level_up()

    def toggle_auto_heal(self):
        self.auto_heal_on_level_up = not getattr(self, 'auto_heal_on_level_up', False)
        if DEBUG:
            print(f"[DEBUG] auto_heal_on_level_up = {self.auto_heal_on_level_up}")

    def level_up(self):
        self.level += 1
        self.exp -= self.exp_to_next_level
        if self.level <= 5:
            self.exp_to_next_level = 3 + (self.level * 2)
        elif self.level <= 10:
            self.exp_to_next_level = 10 + (self.level * 3)
        else:
            self.exp_to_next_level = 20 + (self.level * 5)

        try:
            choices = self.upgrade_weapons(count=3)
            if not choices:
                try:
                    self.prepare_subitem_choices(count=1)
                except Exception:
                    try:
                        self.upgrade_subitems(count=1)
                    except Exception:
                        pass
            else:
                self.awaiting_subitem_choice = False
        except Exception:
            try:
                self.prepare_subitem_choices(count=1)
            except Exception:
                try:
                    self.upgrade_subitems(count=1)
                except Exception:
                    pass

        if getattr(self, 'auto_heal_on_level_up', False):
            self.heal(LEVELUP_HEAL_AMOUNT, "auto")

    def prepare_subitem_choices(self, count=1):
        """サブアイテム選択UIの候補を準備する"""
        tmpl_keys = list(self.subitem_templates.keys())
        if not tmpl_keys:
            return
        if len(self.subitems) >= MAX_SUBITEMS:
            pool = list(self.subitems.keys())
        else:
            pool = list(dict.fromkeys(tmpl_keys + list(self.subitems.keys())))
        num = min(count, len(pool))
        choices = random.sample(pool, num) if num > 0 else []
        self.last_subitem_choices = choices
        self.awaiting_subitem_choice = True
        self.selected_subitem_choice_index = 0
        # Ensure the UI will play the powerup sound when this subitem choice UI is first drawn
        try:
            self._powerup_played_for_subitem_choice = False
        except Exception:
            pass
        if DEBUG:
            print(f"[DEBUG] Subitem choices prepared: {choices}")

    def apply_subitem_choice(self, chosen_key):
        # セーブシステムに記録
        if hasattr(self, 'save_system') and self.save_system:
            try:
                self.save_system.record_subitem_selection(chosen_key)
            except Exception:
                pass
        
        try:
            old_bonus = 0.0
            if chosen_key in self.subitems:
                try:
                    old_bonus = float(self.subitems[chosen_key].value())
                except Exception:
                    old_bonus = 0.0
        except Exception:
            old_bonus = 0.0

        try:
            if chosen_key in self.subitem_templates:
                if chosen_key in self.subitems:
                    self.subitems[chosen_key].level += 1
                    if DEBUG:
                        print(f"[DEBUG] Upgraded subitem: {chosen_key} -> level {self.subitems[chosen_key].level}")
                else:
                    if len(self.subitems) >= MAX_SUBITEMS:
                        if self.subitems:
                            k = random.choice(list(self.subitems.keys()))
                            self.subitems[k].level += 1
                            if DEBUG:
                                print(f"[DEBUG] At max subitems; upgraded existing: {k}")
                    else:
                        template = self.subitem_templates[chosen_key]
                        try:
                            inst = template.copy(level=1)
                        except Exception:
                            inst = type(template)(template.name, base=template.base, per_level=template.per_level, is_percent=getattr(template, 'is_percent', False))
                            inst.level = 1
                        self.subitems[chosen_key] = inst
                        if DEBUG:
                            print(f"[DEBUG] Acquired subitem: {chosen_key}")
            else:
                if DEBUG:
                    print(f"[DEBUG] Unknown subitem chosen: {chosen_key}")
        except Exception:
            pass

        try:
            new_bonus = 0.0
            if chosen_key in self.subitems:
                try:
                    new_bonus = float(self.subitems[chosen_key].value())
                except Exception:
                    new_bonus = 0.0
        except Exception:
            new_bonus = 0.0

        try:
            delta = new_bonus - old_bonus
            if delta != 0 and chosen_key == 'hp':
                add = int(round(delta)) if isinstance(delta, float) else int(delta)
                self.hp = min(self.get_max_hp(), getattr(self, 'hp', 0) + add)
                if DEBUG:
                    print(f"[DEBUG] Applied HP subitem delta: +{add} -> now_hp={self.hp}")
            
            # gem_pickup_rangeを取得した時、magnetの出現率を累積的に1.3倍
            if chosen_key == 'gem_pickup_range' and chosen_key in self.subitems:
                current_level = self.subitems[chosen_key].level
                # 現在の出現率倍率を1.3倍する
                old_multiplier = self.magnet_drop_rate_multiplier
                self.magnet_drop_rate_multiplier = old_multiplier * 1.3
                if DEBUG:
                    print(f"[DEBUG] gem_pickup_range level {current_level}: magnet multiplier {old_multiplier:.6f} -> {self.magnet_drop_rate_multiplier:.6f}")
        except Exception:
            pass

        self.awaiting_subitem_choice = False
        self.last_subitem_choices = []

    def apply_level_choice(self, chosen):
        # セーブシステムに記録
        if hasattr(self, 'save_system') and self.save_system:
            try:
                if isinstance(chosen, str) and ':' in chosen:
                    parts = chosen.split(':', 1)
                    if len(parts) == 2 and parts[0] == 'weapon':
                        self.save_system.record_weapon_selection(parts[1])
            except Exception:
                pass
                
        try:
            typ = 'weapon'
            key = chosen
            if isinstance(chosen, str) and ':' in chosen:
                parts = chosen.split(':', 1)
                if len(parts) == 2:
                    typ, key = parts[0], parts[1]

            if typ == 'weapon':
                if key in getattr(self, 'available_weapons', {}):
                    if len(self.weapons) >= MAX_WEAPONS:
                        if self.weapons:
                            upgrade_target = random.choice(list(self.weapons.keys()))
                            weapon = self.weapons.get(upgrade_target)
                            if weapon and hasattr(weapon, 'level_up'):
                                weapon.level_up()
                                if DEBUG:
                                    print(f"[DEBUG] At max weapons; upgraded existing weapon instead: {upgrade_target}")
                    else:
                        weapon_class = self.available_weapons.pop(key)
                        try:
                            self.weapons[key] = weapon_class()
                        except Exception:
                            try:
                                self.weapons[key] = weapon_class
                            except Exception:
                                pass
                        if DEBUG:
                            print(f"[DEBUG] Player acquired weapon: {key}")
                else:
                    weapon = self.weapons.get(key)
                    if weapon and hasattr(weapon, 'level_up'):
                        try:
                            weapon.level_up()
                            if DEBUG:
                                print(f"[DEBUG] Player upgraded weapon: {key}")
                        except Exception:
                            pass
            elif typ == 'sub':
                try:
                    self.apply_subitem_choice(key)
                except Exception:
                    if key in getattr(self, 'subitem_templates', {}) and key not in self.subitems:
                        try:
                            tmpl = self.subitem_templates[key]
                            inst = tmpl.copy(level=1)
                            self.subitems[key] = inst
                        except Exception:
                            pass
            else:
                if DEBUG:
                    print(f"[DEBUG] Unknown choice type: {typ}")
        except Exception:
            pass
        self.awaiting_weapon_choice = False
        self.last_level_choices = []

    def upgrade_weapons(self, count=3):
        try:
            pool = []
            if len(self.weapons) < MAX_WEAPONS and getattr(self, 'available_weapons', None):
                for k in list(self.available_weapons.keys()):
                    if k in self.weapons:
                        try:
                            if getattr(self.weapons[k], 'level', 1) >= MAX_WEAPON_LEVEL:
                                continue
                        except Exception:
                            pass
                    pool.append(f"weapon:{k}")
            for k in list(self.weapons.keys()):
                try:
                    if getattr(self.weapons[k], 'level', 1) >= MAX_WEAPON_LEVEL:
                        continue
                except Exception:
                    pass
                pool.append(f"weapon:{k}")
            for k in list(getattr(self, 'subitem_templates', {}).keys()):
                if k in self.subitems:
                    try:
                        if getattr(self.subitems[k], 'level', 0) >= MAX_SUBITEM_LEVEL:
                            continue
                    except Exception:
                        pass
                    pool.append(f"sub:{k}")
                else:
                    try:
                        if len(self.subitems) >= MAX_SUBITEMS:
                            continue
                    except Exception:
                        pass
                    pool.append(f"sub:{k}")
            for k in list(self.subitems.keys()):
                try:
                    if getattr(self.subitems[k], 'level', 0) >= MAX_SUBITEM_LEVEL:
                        continue
                except Exception:
                    pass
                pool.append(f"sub:{k}")

            seen = set()
            uniq = []
            for k in pool:
                if k not in seen:
                    seen.add(k)
                    uniq.append(k)
            pool = uniq
            if not pool:
                self.last_level_choices = []
                self.awaiting_weapon_choice = False
                return []
            num = min(count, len(pool))
            choices = random.sample(pool, num) if num > 0 else []
            self.last_level_choices = choices
            self.awaiting_weapon_choice = True
            self.selected_weapon_choice_index = 0
            # Ensure the UI will play the powerup sound when this level-up UI is first drawn
            try:
                self._powerup_played_for_level_choice = False
            except Exception:
                pass
            if DEBUG:
                print(f"[DEBUG] Mixed level choices prepared: {choices}")
            return choices
        except Exception:
            self.last_level_choices = []
            self.awaiting_weapon_choice = False
            return []

    # --- Subitem helpers ---
    def get_max_hp(self):
        try:
            if 'hp' in self.subitems:
                bonus = self.subitems.get('hp').value()
            else:
                bonus = 0
        except Exception:
            bonus = 0
        return int(self.max_hp + bonus)

    def get_base_damage_bonus(self):
        try:
            sub = self.subitems.get('base_damage') if getattr(self, 'subitems', None) is not None else None
            if not sub:
                return 1.0
            if getattr(sub, 'is_percent', False):
                return 1.0 + float(sub.value())
            return 1.0 + float(sub.value())
        except Exception:
            return 1.0

    def get_defense(self):
        try:
            if 'defense' in self.subitems:
                return self.defense + self.subitems.get('defense').value()
            return self.defense
        except Exception:
            return 1

    def get_speed(self):
        try:
            if 'speed' in self.subitems:
                return float(self.base_speed * (1 + self.subitems.get('speed').value()))
            return float(self.base_speed)
        except Exception:
            return 3

    def get_avoidance(self):
        try:
            if 'speed' in self.subitems:
                return self.avoidance + float(self.subitems.get('speed').value())
            return float(self.avoidance)
        except Exception:
            return 0.1

    def get_effect_range_multiplier(self):
        try:
            if 'effect_range' in self.subitems:
                return 1.0 + float(self.subitems.get('effect_range').value())
            return 1.0
        except Exception:
            return 1.0

    def get_effect_time_multiplier(self):
        try:
            if 'effect_time' in self.subitems:
                return 1.0 + float(self.subitems.get('effect_time').value())
            return 1.0
        except Exception:
            return 1.0

    def get_extra_projectiles(self):
        try:
            if 'extra_projectiles' in self.subitems:
                return int(self.subitems.get('extra_projectiles').value())
            return 0
        except Exception:
            return 0

    def get_projectile_speed(self):
        try:
            if 'projectile_speed' in self.subitems:
                return 1.0 + float(self.subitems.get('projectile_speed').value())
            return 1.0
        except Exception:
            return 1.0

    def get_gem_pickup_range(self):
        if 'gem_pickup_range' in self.subitems:
            return float(self.subitems.get('gem_pickup_range').value())
        return 0.0

    def get_gem_collection_speed(self):
        """ジェムの回収速度倍率を取得（projectile_speedサブアイテムレベルに基づく）"""
        if 'projectile_speed' in self.subitems:
            # projectile_speedサブアイテムのレベルに応じてジェム回収速度も向上
            # レベル1で20%アップ、レベル2で40%アップ、レベル3で60%アップ
            return 1.0 + float(self.subitems.get('projectile_speed').value())
        return 1.0

    def get_magnet_level(self):
        """マグネットサブアイテム（gem_pickup_range）のレベルを取得"""
        try:
            if 'gem_pickup_range' in self.subitems:
                return int(self.subitems.get('gem_pickup_range').level)
            return 0
        except Exception:
            return 0

    def upgrade_subitems(self, count=1):
        try:
            return random_upgrade(self.subitems, count=count)
        except Exception:
            return []
    def update_regen(self):
        """自然回復（HPサブアイテム所持時のみ有効）。2秒ごとに1回復。"""
        try:
            now = pygame.time.get_ticks()
            # 死亡中は回復しない
            if getattr(self, 'hp', 0) <= 0:
                self.last_regen_ms = now
                return
            if 'hp' in self.subitems and self.hp < self.get_max_hp():
                # 自然回復：設定された間隔で回復
                if now - getattr(self, 'last_regen_ms', 0) >= NATURAL_HEAL_INTERVAL_MS:
                    # HPサブアイテムのレベルに応じた回復量を取得
                    natural_heal_amount = self.get_natural_heal_amount()
                    heal_amount = self.heal(natural_heal_amount, "auto")
                    self.last_regen_ms = now
                    
                    # デバッグログ
                    if heal_amount > 0:
                        print(f"[DEBUG] Natural heal: {heal_amount} HP (Level {self.subitems['hp'].level if 'hp' in self.subitems else 0}) at ({self.x}, {self.y})")
        except Exception:
            pass

    def heal(self, amount, heal_type="normal"):
        """共通の回復処理
        
        Args:
            amount: 回復量または割合（heal_typeが"item"の場合は割合）
            heal_type: 回復の種類 ("normal", "auto", "garlic", "item")
        
        Returns:
            実際の回復量
        """
        # ヒールアイテムの場合は割合計算
        if heal_type == "item":
            heal_amount = int(self.get_max_hp() * amount)  # 割合から実数値に変換
        else:
            heal_amount = amount
        
        old_hp = self.hp
        self.hp = min(self.get_max_hp(), self.hp + heal_amount)
        actual_heal = self.hp - old_hp
        
        if actual_heal > 0 and hasattr(self, 'heal_effect_callback') and callable(self.heal_effect_callback):
            is_auto = heal_type in ["auto", "garlic"]  # 自動回復系はAutoHealEffectも表示
            self.heal_effect_callback(self.x, self.y, actual_heal, is_auto=is_auto)
            
        return actual_heal

    def get_natural_heal_amount(self):
        """自然回復量を取得（HPサブアイテムのレベルに応じて増加）"""
        base_heal = NATURAL_HEAL_AMOUNT  # 基本回復量: 1
        
        if 'hp' in self.subitems:
            hp_subitem = self.subitems['hp']
            hp_level = getattr(hp_subitem, 'level', 0)
            # HPサブアイテムのレベル1につき回復量+1
            return base_heal + hp_level
        
        return base_heal

    def get_garlic_heal_amount(self):
        """ガーリック回復量を取得（固定値）"""
        return GARLIC_HEAL_AMOUNT  # 基本回復量: 1（HPサブアイテムの影響を受けない）

    def activate_magnet(self):
        """マグネット効果を有効化"""
        current_time = pygame.time.get_ticks()
        self.magnet_active = True
        self.magnet_end_time = current_time + MAGNET_EFFECT_DURATION_MS

    def update_magnet_effect(self):
        """マグネット効果の状態を更新"""
        if self.magnet_active:
            current_time = pygame.time.get_ticks()
            if current_time >= self.magnet_end_time:
                self.magnet_active = False

    def is_magnet_active(self):
        """マグネット効果が有効かどうかを返す"""
        return self.magnet_active

    def get_magnet_drop_rate(self):
        """現在のmagnetアイテムの出現率を取得（基本出現率×倍率）"""
        from constants import MAGNET_ITEM_DROP_RATE
        return MAGNET_ITEM_DROP_RATE * self.magnet_drop_rate_multiplier

    def activate_screen_shake(self, intensity=None):
        """画面揺れエフェクトを有効化"""
        current_time = pygame.time.get_ticks()
        self.screen_shake_active = True
        self.screen_shake_end_time = current_time + SCREEN_SHAKE_DURATION_MS
        self.screen_shake_intensity = intensity if intensity is not None else SCREEN_SHAKE_INTENSITY

    def update_screen_shake(self):
        """画面揺れエフェクトの状態を更新"""
        if self.screen_shake_active:
            current_time = pygame.time.get_ticks()
            if current_time >= self.screen_shake_end_time:
                self.screen_shake_active = False
                self.screen_shake_intensity = 0

    def get_screen_shake_offset(self):
        """現在の画面揺れオフセットを取得"""
        if not self.screen_shake_active:
            return (0, 0)
        
        import random
        # 時間経過で強度を減衰
        current_time = pygame.time.get_ticks()
        remaining_time = max(0, self.screen_shake_end_time - current_time)
        time_ratio = remaining_time / SCREEN_SHAKE_DURATION_MS
        current_intensity = self.screen_shake_intensity * time_ratio
        
        # ランダムなオフセット
        offset_x = random.uniform(-current_intensity, current_intensity)
        offset_y = random.uniform(-current_intensity, current_intensity)
        return (int(offset_x), int(offset_y))

    def set_input_method(self, method):
        """入力メソッドを設定（キーボードカーソル表示制御用）"""
        if method in ["keyboard", "mouse"]:
            self.last_input_method = method
            self.show_keyboard_cursor = (method == "keyboard")

    def should_show_keyboard_cursor(self):
        """キーボードカーソルを表示すべきかどうか"""
        return self.show_keyboard_cursor
    
    def _adjust_spawn_position(self):
        """障害物のない安全な開始位置に調整（マップが有効な場合のみ）"""
        if not USE_CSV_MAP:
            return  # マップが無効な場合は何もしない
            
        try:
            from stage import get_stage_map
            stage_map = get_stage_map()
            
            # 安全な開始位置を見つける
            safe_x, safe_y = stage_map.find_safe_spawn_position(self.x, self.y, self.size)
            
            # デバッグ出力
            if safe_x != self.x or safe_y != self.y:
                print(f"[INFO] Player spawn adjusted from ({self.x:.0f}, {self.y:.0f}) to ({safe_x:.0f}, {safe_y:.0f})")
            
            self.x = safe_x
            self.y = safe_y
        except Exception as e:
            # ステージが初期化されていない場合はそのまま
            print(f"[WARNING] Could not adjust spawn position: {e}")
            pass