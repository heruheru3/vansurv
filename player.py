# filepath: e:\jupy_work\vansurv\player.py
import pygame
import math
import random
from constants import *  # 相対インポートを絶対インポートに変更
from weapons.melee import Whip, Garlic
from weapons.projectile import HolyWater, MagicWand, Axe, Stone, RotatingBook, Knife, Thunder
from subitems import get_default_subitems, random_upgrade

class Player:
    def __init__(self, screen):
        self.screen = screen
        # 初期位置をワールド中心に変更
        self.x = WORLD_WIDTH // 2
        self.y = WORLD_HEIGHT // 2
        self.speed = 3
        # 基本速度（サブアイテムで増加する）
        self.base_speed = 3
        self.size = 32
        # 基本最大HP と現在HP（サブアイテムで最大HPが増える）
        self.max_hp = 100
        self.hp = self.max_hp
        self.exp = 0
        self.level = 1
        self.exp_to_next_level = 3

        # 利用可能な初期武器の定義
        initial_weapons = {
            'magic_wand': MagicWand,
            'stone': Stone,
            'whip': Whip,
        }

        # 全武器の定義
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

        # 初期状態：武器は空。ゲーム開始時に3択UIで選ばせるため、available_weaponsに全武器をセットする
        self.weapons = {}
        self.available_weapons = all_weapons.copy()

        self.active_attacks = []

        self.target_x = self.x  # マウス移動用の目標X座標
        self.target_y = self.y  # マウス移動用の目標Y座標
        self.mouse_control = False  # マウス制御フラグ
        self.movement_deadzone = 10  # 移動停止する距離のしきい値
        # マウス移動の速度をキーボードと同じにするためのフラグ（倍率は1に固定）
        self.mouse_speed_multiplier = 1.0
        self.mouse_distance_scaling = False
        # 動き検出用の速度ベクトル
        self.vx = 0.0
        self.vy = 0.0
        # 回転するオーブ用のサーフェスを作成
        orb_size = max(32, self.size * 3)
        self.orb_base = pygame.Surface((orb_size, orb_size), pygame.SRCALPHA)
        cx, cy = orb_size // 2, orb_size // 2
        # 上から見た「転がる球体」を表現するため、中央に赤道バンドを描く
        # 中央のバンドはやや暗めで半透明にして、回転させることで転がり感を出す
        # ベースの淡いグロー
        for i in range(orb_size//2, 0, -1):
            t = i / (orb_size//2)
            glow_col = (30 + int(50 * t), 140 + int(80 * t), 80 + int(80 * t), int(20 * t))
            pygame.draw.circle(self.orb_base, glow_col, (cx, cy), i)
        # 赤道バンド（やや暗めの帯）
        band_rect = (0, int(orb_size * 0.42), orb_size, int(orb_size * 0.16))
        pygame.draw.ellipse(self.orb_base, (20, 90, 60, 180), band_rect)
        # バンド上に小さなマーキングを付けて回転で模様が動いているように見せる
        mark_count = 10
        for m in range(mark_count):
            ang = (2 * math.pi * m) / mark_count
            mx = cx + int(math.cos(ang) * orb_size * 0.38)
            my = cy + int(math.sin(ang) * orb_size * 0.02)
            pygame.draw.circle(self.orb_base, (40, 130, 90, 220), (mx, my), max(1, orb_size // 20))
        self.orb_angle = 0.0
        # 転がり計算用: 前回位置と累積距離
        self.prev_x = float(self.x)
        self.prev_y = float(self.y)
        self.distance_traveled = 0.0

        # プレイヤー用チップセットの読み込み（幅64px、16pxごとに4フレーム）
        # ファイル名はプロジェクトルートの "player_chip.png" を想定します。存在しない場合はフォールバック描画を使用します。
        try:
            sheet = pygame.image.load("player_chip.png").convert_alpha()
            sheet_w = sheet.get_width()
            sheet_h = sheet.get_height()
            tile_w = 16
            # 横幅が64を想定。16pxごとにフレームを切り出す（0,16,32,48）
            self.frames = []
            for x in range(0, min(sheet_w, 64), tile_w):
                # 高さは画像の全高を使う（一般的に16か32）
                frame = sheet.subsurface((x, 0, tile_w, sheet_h)).copy()
                self.frames.append(frame)
            if not self.frames:
                raise Exception("no frames")
        except Exception:
            # 読み込み失敗時は空のリストにして既存の円描画をフォールバックで使う
            self.frames = []

        # アニメーション制御
        self.frame_index = 0
        self.anim_tick = 0
        self.anim_speed = 6  # draw() 呼び出しごとのティック数。小さいほど早く回る
        self.facing = 'left'  # 'left' or 'right'

        # レベルアップ時の自動回復をオン/オフするフラグ（デフォルトは False: 自動回復しない）
        self.auto_heal_on_level_up = False

        # サブアイテムの初期化
        try:
            # テンプレート群（全候補）と、プレイヤーの所持サブアイテムを分ける
            self.subitem_templates = get_default_subitems()
        except Exception:
            self.subitem_templates = {}
        # 実際にプレイヤーが所持しているサブアイテム（キー -> SubItem インスタンス）
        self.subitems = {}

        # レベルアップ時の武器選択用（UI表示のための候補と状態）
        self.last_level_choices = []
        self.awaiting_weapon_choice = False
        # レベルアップ時のサブアイテム選択用状態
        self.last_subitem_choices = []
        self.awaiting_subitem_choice = False

        # ゲーム開始時に武器選択の3択UIを表示する
        try:
            self.upgrade_weapons()
        except Exception:
            pass

    def move(self, camera_x=0, camera_y=0):
        dx = 0.0
        dy = 0.0
        # キーボード入力の処理（方向ベクトルとして扱う）
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            dx -= 1.0
        if keys[pygame.K_RIGHT]:
            dx += 1.0
        if keys[pygame.K_UP]:
            dy -= 1.0
        if keys[pygame.K_DOWN]:
            dy += 1.0

        # マウス入力の処理（左クリックでマウス移動）
        if pygame.mouse.get_pressed()[0]:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            # 画面座標のマウス位置をワールド座標に変換
            world_mouse_x = mouse_x + camera_x
            world_mouse_y = mouse_y + camera_y
            mouse_dx = world_mouse_x - self.x
            mouse_dy = world_mouse_y - self.y
            distance = math.hypot(mouse_dx, mouse_dy)

            if distance > self.movement_deadzone:
                # マウス方向を単位ベクトルにする
                dir_x = mouse_dx / distance
                dir_y = mouse_dy / distance
                # マウス入力はキーボード入力に加算する（両方同時に影響）
                dx += dir_x * self.mouse_speed_multiplier
                dy += dir_y * self.mouse_speed_multiplier

        # ベクトルの長さを求め、0でなければ正規化して self.speed を掛ける
        length = math.hypot(dx, dy)
        effective_speed = self.get_speed()
        if length > 0:
            nx = dx / length
            ny = dy / length
            self.x += nx * effective_speed
            self.y += ny * effective_speed
            # 速度ベクトルを保存（描画で回転アニメに使う）
            self.vx = nx * effective_speed
            self.vy = ny * effective_speed
        else:
            self.vx = 0.0
            self.vy = 0.0
            # どちらの入力も無ければ速度0（位置は変わらない)

        # 画面端での位置制限（ワールド境界に変更）
        self.x = max(self.size, min(self.x, WORLD_WIDTH - self.size))
        self.y = max(self.size, min(self.y, WORLD_HEIGHT - self.size))

        # 移動距離を累積して転がり量に変換
        dxp = self.x - self.prev_x
        dyp = self.y - self.prev_y
        moved = math.hypot(dxp, dyp)
        if moved > 0:
            self.distance_traveled += moved
        self.prev_x = float(self.x)
        self.prev_y = float(self.y)

    def update(self):
        # キーボードとマウスの入力を処理
        keys = pygame.key.get_pressed()
        mouse_buttons = pygame.mouse.get_pressed()
        mouse_x, mouse_y = pygame.mouse.get_pos()

        # マウスの右クリックで移動モード切替
        mouse_click = pygame.mouse.get_pressed()[2]  # 右クリック
        if mouse_click:
            self.mouse_control = not self.mouse_control

        if self.mouse_control:
            # マウス制御モード
            if mouse_buttons[0]:  # 左クリックで移動
                self.target_x = mouse_x
                self.target_y = mouse_y

            # 目標位置との距離を計算
            dx = self.target_x - self.x
            dy = self.target_y - self.y
            distance = math.sqrt(dx*dx + dy*dy)

            # 一定距離以上なら移動
            if distance > self.movement_deadzone:
                # 正規化して移動
                self.x += (dx / distance) * self.speed
                self.y += (dy / distance) * self.speed
                self.vx = (dx / distance) * self.speed
                self.vy = (dy / distance) * self.speed
            else:
                self.vx = 0.0
                self.vy = 0.0
        else:
            # キーボード制御モード
            dx = 0
            dy = 0
            if keys[pygame.K_LEFT]:
                dx = -1
            if keys[pygame.K_RIGHT]:
                dx = 1
            if keys[pygame.K_UP]:
                dy = -1
            if keys[pygame.K_DOWN]:
                dy = 1

            # 斜め移動の正規化
            if dx != 0 and dy != 0:
                dx *= 0.707  # 1/√2
                dy *= 0.707

            sp = self.get_speed()
            self.x += dx * sp
            self.y += dy * sp
            self.vx = dx * sp
            self.vy = dy * sp

    def update_attacks(self, enemies, camera_x=None, camera_y=None):
        # 期限切れの攻撃を削除
        self.active_attacks = [attack for attack in self.active_attacks 
                             if not attack.is_expired()]
        
        # 各武器の攻撃を実行
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

            # 判定ルール:
            # - attack が 'enemies' という名前のパラメータを受け取るなら enemies を渡す
            # - そうでなければ enemies を渡さない
            # さらに camera_x/camera_y をキーワード引数として渡せる場合は渡す
            try:
                if 'enemies' in params:
                    # enemies を受け取る武器 (Thunder, MagicWand 等)
                    try:
                        new_attacks = atk_fn(self, enemies, camera_x=camera_x, camera_y=camera_y)
                    except TypeError:
                        try:
                            new_attacks = atk_fn(self, enemies)
                        except Exception:
                            new_attacks = []
                else:
                    # enemies を受け取らない武器 (Whip 等)
                    try:
                        # camera_x/camera_y を受け取るか確認してキーワードで渡す
                        if 'camera_x' in params or 'camera_y' in params:
                            new_attacks = atk_fn(self, camera_x=camera_x, camera_y=camera_y)
                        else:
                            new_attacks = atk_fn(self)
                    except TypeError:
                        try:
                            new_attacks = atk_fn(self)
                        except Exception:
                            new_attacks = []
            except Exception:
                new_attacks = []

            if new_attacks:
                self.active_attacks.extend(new_attacks)

        # 攻撃エフェクトの更新（カメラ座標を渡す）
        for attack in self.active_attacks:
            try:
                attack.update(camera_x, camera_y)
            except TypeError:
                # 旧インターフェースに対応
                attack.update()

    def draw(self, screen, camera_x=0, camera_y=0):
        # ワールド→スクリーン座標
        sx = int(self.x - camera_x)
        sy = int(self.y - camera_y)

        # 影を描画（地面に接している感を出す）
        r = self.size
        # 変更: 影をプレイヤーサイズ程度に縮小し、より薄い半透明の黒にする
        shadow_w, shadow_h = int(r * 2), int(max(1, r * 0.9))
        shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
        # 半透明の黒（alpha 120）で描画
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 120), (0, 0, shadow_w, shadow_h))
        # 影はプレイヤーよりさらに下に表示（オフセットを大きくして地面に近く見せる）
        shadow_rect = shadow_surf.get_rect(center=(int(sx), int(sy + r * 1.0)))
        screen.blit(shadow_surf, shadow_rect.topleft)

        # スプライトチップがある場合はそれを使ってアニメーション
        # 向き判定: vx が負なら左向き、正なら右向き。停止中は向きを保持
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
                # 停止時は最初のフレームに戻す
                self.frame_index = 0
                self.anim_tick = 0

            frame = self.frames[self.frame_index]
            # サイズをプレイヤーの半径に合わせてスケーリング
            target_size = (int(r*2), int(r*2))
            # アンチエイリアスなしで拡大（ピクセルのハードな輪郭を保持）
            frame_s = pygame.transform.scale(frame, target_size)
            if self.facing == 'right':
                frame_s = pygame.transform.flip(frame_s, True, False)
            screen.blit(frame_s, (int(sx - r), int(sy - r)))

            # 軽いハイライトをスプライト上に描画して立体感を維持
            hl_surf = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(hl_surf, (220, 250, 220, 12), (r, r), max(1, r//3))
            hx = int(sx - (self.vx * 2.5))
            hy = int(sy - (self.vy * 2.5) - r*0.12)
            screen.blit(hl_surf, (hx - r, hy - r))

        else:
            # フォールバック: 既存のトップダウングラデ（球体の上面）を描画
            surf = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            base = (50, 200, 80)
            darker = tuple(max(0, int(c * 0.45)) for c in base)
            for i in range(r, 0, -1):
                t = i / r
                col = tuple(int(darker[j] + (base[j] - darker[j]) * t) for j in range(3))
                alpha = int(100 * (0.4 + 0.6 * t))
                pygame.draw.circle(surf, col + (alpha,), (r, r), i)
            pygame.draw.circle(surf, (0, 0, 0, 100), (r, r), r, 1)
            screen.blit(surf, (int(sx - r), int(sy - r)))

            # 回転（転がり）：累積移動距離から物理的に角度を算出して回転させる（視覚効果）
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

            # 球体上の微妙なハイライト（移動方向の逆側に薄く表示）
            speed = math.hypot(self.vx, self.vy)
            hx = int(sx - (self.vx * 2.5))
            hy = int(sy - (self.vy * 2.5) - r*0.12)
            hl_surf = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(hl_surf, (220, 250, 220, 18), (r, r), max(1, r//3))
            screen.blit(hl_surf, (hx - r, hy - r))

            if self.distance_traveled > radius * math.pi * 2:
                self.distance_traveled %= (radius * math.pi * 2)

    def draw_attacks(self, screen, camera_x=0, camera_y=0):
        for attack in self.active_attacks:
            try:
                attack.draw(screen, camera_x, camera_y)
            except TypeError:
                # 旧インターフェースに対応
                attack.draw(screen)

    def add_exp(self, amount):
        self.exp += amount
        if self.exp >= self.exp_to_next_level:
            self.level_up()

    def toggle_auto_heal(self):
        """レベルアップ時の自動回復フラグをトグルするユーティリティ。デバッグ出力あり."""
        self.auto_heal_on_level_up = not getattr(self, 'auto_heal_on_level_up', False)
        try:
            if DEBUG:
                print(f"[DEBUG] auto_heal_on_level_up = {self.auto_heal_on_level_up}")
        except Exception:
            pass

    def level_up(self):
        self.level += 1
        self.exp -= self.exp_to_next_level
        # レベルに応じて必要経験値を増加
        if self.level <= 5:
            self.exp_to_next_level = 3 + (self.level * 2)  # レベル5まで: 3, 5, 7, 9, 11
        elif self.level <= 10:
            self.exp_to_next_level = 10 + (self.level * 3)  # レベル6-10: 13, 16, 19, 22, 25
        else:
            self.exp_to_next_level = 20 + (self.level * 5)  # レベル11以降: 30, 35, 40...

        # レベルアップ時は武器とサブアイテムの混合候補を表示する（3択）
        try:
            # まず混合プールから3択を準備する
            choices = self.upgrade_weapons(count=3)
            # 混合候補が作れなければサブアイテム選択にフォールバック
            if not choices:
                try:
                    self.prepare_subitem_choices(count=1)
                except Exception:
                    try:
                        self.upgrade_subitems(count=1)
                    except Exception:
                        pass
            else:
                # 混合候補が用意できたらサブアイテム選択フラグをクリアしておく
                self.awaiting_subitem_choice = False
        except Exception:
            # 何か失敗したら最終的にサブアイテムを用意する
            try:
                self.prepare_subitem_choices(count=1)
            except Exception:
                try:
                    self.upgrade_subitems(count=1)
                except Exception:
                    pass

        # 自動回復フラグが有効な場合は最大HPに応じて回復
        if getattr(self, 'auto_heal_on_level_up', False):
            self.hp = min(self.get_max_hp(), self.hp + 20)

        # 互換性のため、既存コードで武器アップグレードを行っていた場合の処理は
        # upgrade_weapons() 内で候補作成のみを行っていてここでは追加処理を行わない

    def prepare_subitem_choices(self, count=1):
        """レベルアップ時にサブアイテム選択UI用の候補を準備する。
        count: 表示する候補数（通常は1だが拡張可能）
        候補はテンプレートからランダムに選ぶ。既に所持しているサブアイテムは「Upgrade」として、
        未所持のものは取得候補として表示する。所持上限(MAX_SUBITEMS)に達しているときは
        新規取得候補は表示せず、既存所持の強化のみ候補に含める。
        """
        tmpl_keys = list(self.subitem_templates.keys())
        if not tmpl_keys:
            return

        # 候補プールを作る
        if len(self.subitems) >= MAX_SUBITEMS:
            pool = list(self.subitems.keys())
        else:
            pool = list(dict.fromkeys(tmpl_keys + list(self.subitems.keys())))

        num = min(count, len(pool))
        choices = random.sample(pool, num)
        self.last_subitem_choices = choices
        self.awaiting_subitem_choice = True
        if DEBUG:
            print(f"[DEBUG] Subitem choices prepared: {choices}")

    def apply_subitem_choice(self, chosen_key):
        """UI から渡された選択を適用する。
        chosen_key は subitem のキー名（'hp' など）。
        所持上限に達している場合、新規選択は既存のものをランダム強化に変換する。
        """
        # 変更前の効果量を取得（差分を計算して current HP に反映するため）
        try:
            old_bonus = 0.0
            if chosen_key in self.subitems:
                try:
                    old_bonus = float(self.subitems[chosen_key].value())
                except Exception:
                    old_bonus = 0.0
            else:
                old_bonus = 0.0
        except Exception:
            old_bonus = 0.0

        try:
            if chosen_key in self.subitem_templates:
                # 新規取得もしくは既存強化
                if chosen_key in self.subitems:
                    # 既に持っているものはレベルアップ
                    self.subitems[chosen_key].level += 1
                    if DEBUG:
                        print(f"[DEBUG] Upgraded subitem: {chosen_key} -> level {self.subitems[chosen_key].level}")
                else:
                    # 所持上限に達している場合はフォールバックして既存のものを強化
                    if len(self.subitems) >= MAX_SUBITEMS:
                        if self.subitems:
                            k = random.choice(list(self.subitems.keys()))
                            self.subitems[k].level += 1
                            if DEBUG:
                                print(f"[DEBUG] At max subitems; upgraded existing: {k}")
                    else:
                        # テンプレートから実インスタンスを作って追加
                        template = self.subitem_templates[chosen_key]
                        try:
                            inst = template.copy(level=1)
                        except Exception:
                            # 互換性のため、手動で作る
                            inst = type(template)(template.name, base=template.base, per_level=template.per_level, is_percent=getattr(template, 'is_percent', False))
                            inst.level = 1
                        self.subitems[chosen_key] = inst
                        if DEBUG:
                            print(f"[DEBUG] Acquired subitem: {chosen_key}")
            else:
                # 予期しないキーは無視
                if DEBUG:
                    print(f"[DEBUG] Unknown subitem chosen: {chosen_key}")
        except Exception:
            pass

        # 変更後の効果量を取得し、HP の差分を現在の HP に反映する
        try:
            new_bonus = 0.0
            if chosen_key in self.subitems:
                try:
                    new_bonus = float(self.subitems[chosen_key].value())
                except Exception:
                    new_bonus = 0.0
            else:
                new_bonus = 0.0
        except Exception:
            new_bonus = 0.0

        # 差分を現在の HP に反映（'hp' のみ）
        try:
            delta = new_bonus - old_bonus
            if delta != 0 and chosen_key == 'hp':
                # delta は float の可能性があるが HP は整数と考える。四捨五入して反映。
                try:
                    add = int(round(delta))
                except Exception:
                    add = int(delta)
                # 現在 HP を増やす（最大値を超えないように clamp）
                try:
                    self.hp = min(self.get_max_hp(), getattr(self, 'hp', 0) + add)
                except Exception:
                    # 万が一の型エラーに備えて直接演算
                    self.hp = min(self.get_max_hp(), (self.hp if hasattr(self, 'hp') else 0) + add)
                if DEBUG:
                    print(f"[DEBUG] Applied HP subitem delta: old={old_bonus} new={new_bonus} add_hp={add} now_hp={self.hp}")
        except Exception:
            pass

        self.awaiting_subitem_choice = False
        self.last_subitem_choices = []

    def apply_level_choice(self, chosen):
        """UI から選択された候補を適用する。
        支持する形式:
          - 'weapon:<key>' -> 武器取得/強化
          - 'sub:<key>' -> サブアイテム取得/強化
        互換性のため、従来のキー名のみも受け付ける（weapon として扱う）。
        """
        try:
            typ = 'weapon'
            key = chosen
            if isinstance(chosen, str) and ':' in chosen:
                parts = chosen.split(':', 1)
                if len(parts) == 2:
                    typ, key = parts[0], parts[1]

            if typ == 'weapon':
                # 新規武器を取得する場合
                if key in getattr(self, 'available_weapons', {}):
                    if len(self.weapons) >= MAX_WEAPONS:
                        # 上限の場合はランダムな既存武器を強化
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
                    # 所持武器の強化
                    weapon = self.weapons.get(key)
                    if weapon and hasattr(weapon, 'level_up'):
                        try:
                            weapon.level_up()
                            if DEBUG:
                                print(f"[DEBUG] Player upgraded weapon: {key}")
                        except Exception:
                            pass

            elif typ == 'sub':
                # サブアイテムの取得/強化処理に委譲
                try:
                    self.apply_subitem_choice(key)
                except Exception:
                    # フォールバックとして直接操作
                    if key in getattr(self, 'subitem_templates', {}) and key not in self.subitems:
                        try:
                            tmpl = self.subitem_templates[key]
                            inst = tmpl.copy(level=1)
                            self.subitems[key] = inst
                        except Exception:
                            pass

            else:
                # 不明なタイプは無視
                if DEBUG:
                    print(f"[DEBUG] Unknown choice type: {typ}")
        except Exception:
            pass
        # UI 状態をクリア
        self.awaiting_weapon_choice = False
        self.last_level_choices = []

    def upgrade_weapons(self, count=3):
        """Prepare mixed choices (weapons and subitems) for level-up UI.
        Choices are strings with a prefix to indicate type:
          - 'weapon:<key>' for weapons
          - 'sub:<key>' for subitems
        This keeps UI and apply_level_choice compatible while allowing mixed pools.
        """
        try:
            pool = []
            # If player can still acquire new weapons, include available ones
            if len(self.weapons) < MAX_WEAPONS and getattr(self, 'available_weapons', None):
                for k in list(self.available_weapons.keys()):
                    pool.append(f"weapon:{k}")
            # Include existing weapons as possible upgrade targets
            for k in list(self.weapons.keys()):
                pool.append(f"weapon:{k}")
            # Include subitem templates (new possible subitems)
            for k in list(getattr(self, 'subitem_templates', {}).keys()):
                pool.append(f"sub:{k}")
            # Also include existing owned subitems as upgrade targets
            for k in list(self.subitems.keys()):
                pool.append(f"sub:{k}")

            # Deduplicate while preserving order
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
            choices = random.sample(pool, num)
            self.last_level_choices = choices
            self.awaiting_weapon_choice = True
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
                # 所持していなければテンプレートの値を 0 として扱う
                bonus = 0
        except Exception:
            bonus = 0
        return int(self.max_hp + bonus)

    def get_base_damage_bonus(self):
        try:
            sub = self.subitems.get('base_damage') if getattr(self, 'subitems', None) is not None else None
            if not sub:
                return 1.0
            # If the subitem is percent-type, interpret value() as a fractional bonus (e.g. 0.2 => +20%)
            if getattr(sub, 'is_percent', False):
                return 1.0 + float(sub.value())
            # Otherwise treat it as a flat additive bonus expressed as a multiplier (e.g. +20 => +20%)
            return 1.0 + float(sub.value())
        except Exception:
            return 1.0

    def get_defense(self):
        try:
            if 'defense' in self.subitems:
                return self.subitems.get('defense').value()
            return 0
        except Exception:
            return 0

    def get_speed(self):
        try:
            if 'speed' in self.subitems:
                return float(self.base_speed + self.subitems.get('speed').value())
            return float(self.base_speed)
        except Exception:
            return float(self.base_speed)

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
        """射出物の速度に対する倍率を返す。サブアイテム 'projectile_speed' がある場合は 1.0 + value() を返す。
        """
        try:
            if 'projectile_speed' in self.subitems:
                return 1.0 + float(self.subitems.get('projectile_speed').value())
            return 1.0
        except Exception:
            return 1.0

    def upgrade_subitems(self, count=1):
        try:
            return random_upgrade(self.subitems, count=count)
        except Exception:
            return []