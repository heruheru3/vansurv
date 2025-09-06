# filepath: e:\jupy_work\vansurv\effects\items.py
import pygame
import math
import random
from constants import *
from resources import load_icons


class ExperienceGem:
    def __init__(self, x, y, value=1):
        self.x = x
        self.y = y
        self.type = "experience"
        self.size = 8
        self.speed = 6
        self.collected = False
        # ジェムが持つ経験値量（デフォルト1）
        self.value = int(max(1, value))

    def move_to_player(self, player):
        dx = player.x - self.x
        dy = player.y - self.y
        distance = math.sqrt(dx**2 + dy**2)
        
        # 引き寄せ開始距離をサブアイテムで拡張可能にする
        try:
            extra = float(player.get_gem_pickup_range()) if hasattr(player, 'get_gem_pickup_range') else 0.0
        except Exception:
            extra = 0.0
        attract_threshold = 100.0 + extra
        
        # マグネット効果が有効な場合、全画面からの引き寄せ＋速度アップ
        if hasattr(player, 'is_magnet_active') and player.is_magnet_active():
            attract_threshold = float('inf')  # 距離制限なし
            speed_multiplier = MAGNET_FORCE_MULTIPLIER
        else:
            speed_multiplier = 1.0

        if distance < attract_threshold and distance != 0:
            move_speed = self.speed * speed_multiplier
            self.x += (dx / distance) * move_speed
            self.y += (dy / distance) * move_speed

    def draw(self, screen, camera_x=0, camera_y=0):
        # ジェムの色を value に応じて変更する
        try:
            val = int(max(1, self.value))
        except Exception:
            val = 1
        if val == 1:
            base_col = CYAN
        elif 2 <= val <= 5:
            base_col = GREEN
        else:
            base_col = RED

        # ジェムを小さなひし形（ダイヤ）にしてグローを付ける
        r = max(4, self.size // 2)
        w = h = r * 6
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        cx, cy = w // 2, h // 2
        # 背景グロー（同心楕円でやわらかく）
        for i in range(r*3, 0, -1):
            t = i / (r*3)
            alpha = int(10 + (1 - t) * 180)
            col = (base_col[0], base_col[1], base_col[2], alpha)
            try:
                pygame.draw.ellipse(surf, col, (cx - int(t*r*2.2), cy - int(t*r*2.2), int(t*r*4.4), int(t*r*4.4)))
            except Exception:
                pass
        # ひし形の頂点（ローカル座標）
        points = [
            (cx, cy - r),
            (cx + r, cy),
            (cx, cy + r),
            (cx - r, cy)
        ]
        # 本体
        try:
            pygame.draw.polygon(surf, base_col + (240,), points)
        except Exception:
            # まれに tuple + (int,) でエラーが出る環境があるため安全策
            pygame.draw.polygon(surf, (base_col[0], base_col[1], base_col[2], 240), points)
        # ハイライト
        hl = (min(255, base_col[0]+80), min(255, base_col[1]+80), min(255, base_col[2]+80), 140)
        try:
            pygame.draw.polygon(surf, hl, [
                (cx, cy - r),
                (cx + int(r*0.5), cy - int(r*0.2)),
                (cx, cy + int(r*0.2)),
                (cx - int(r*0.5), cy - int(r*0.2))
            ])
        except Exception:
            pass
        # 線で輪郭
        try:
            pygame.draw.polygon(surf, (0,0,0,100), points, 1)
        except Exception:
            pass
        screen.blit(surf, (int(self.x - cx - camera_x), int(self.y - cy - camera_y)))

class GameItem:
    def __init__(self, x, y, item_type):
        self.x = x
        self.y = y
        self.size = 12
        self.speed = 2
        self.type = item_type
        self.collected = False
        
        # 出現アニメーション用
        self.spawn_time = pygame.time.get_ticks()
        self.spawn_scale = 0.0  # 開始時はサイズ0
        self.spawn_duration = 300  # 出現アニメーション時間（ミリ秒）
        
        # アイテム画像を読み込む
        try:
            icons = load_icons(size=48, icon_names=[item_type])  # サイズを48に倍増
            self.image = icons.get(item_type)
        except Exception:
            self.image = None

    def move_to_player(self, player):
        dx = player.x - self.x
        dy = player.y - self.y
        distance = math.sqrt(dx**2 + dy**2)
        
        # アイテムの引き寄せも同様にサブアイテムで拡張
        try:
            extra = float(player.get_gem_pickup_range()) if hasattr(player, 'get_gem_pickup_range') else 0.0
        except Exception:
            extra = 0.0
        attract_threshold = 100.0 + extra

        if distance < attract_threshold and distance != 0:
            self.x += (dx / distance) * self.speed
            self.y += (dy / distance) * self.speed

    def draw(self, screen, camera_x=0, camera_y=0):
        # 出現アニメーションのスケール計算
        current_time = pygame.time.get_ticks()
        time_since_spawn = current_time - self.spawn_time
        
        if time_since_spawn < self.spawn_duration:
            # 出現アニメーション中：0から1にスケール
            progress = time_since_spawn / self.spawn_duration
            self.spawn_scale = min(1.0, progress * 1.2)  # 少しオーバーシュート
        else:
            self.spawn_scale = 1.0
        
        # スケールが0の場合は描画しない
        if self.spawn_scale <= 0:
            return
            
        # 画像が読み込まれている場合は画像を使用
        if self.image:
            # 画像のサイズに基づいて描画位置を調整（スケール適用）
            img_w, img_h = self.image.get_size()
            scaled_w = int(img_w * self.spawn_scale)
            scaled_h = int(img_h * self.spawn_scale)
            
            # スケールされた画像を作成
            if scaled_w > 0 and scaled_h > 0:
                scaled_image = pygame.transform.scale(self.image, (scaled_w, scaled_h))
                draw_x = int(self.x - scaled_w // 2 - camera_x)
                draw_y = int(self.y - scaled_h // 2 - camera_y)
                
                # 画像の中心座標
                center_x = int(self.x - camera_x)
                center_y = int(self.y - camera_y)
                
                # ピンクの円の半径（スケール適用）
                circle_radius = int(max(scaled_w, scaled_h) * 0.35)
                
                # グロー効果（複数の円を重ねて描画）
                glow_color = (255, 20, 147, 30)  # DeepPink with low alpha
                for i in range(5):
                    glow_radius = circle_radius + (i + 1) * 3
                    glow_alpha = max(10, int((40 - i * 8) * self.spawn_scale))
                    glow_surf = pygame.Surface((glow_radius * 2 + 10, glow_radius * 2 + 10), pygame.SRCALPHA)
                    pygame.draw.circle(glow_surf, (255, 20, 147, glow_alpha), 
                                     (glow_radius + 5, glow_radius + 5), glow_radius)
                    screen.blit(glow_surf, (center_x - glow_radius - 5, center_y - glow_radius - 5))
                
                # メインのピンクの円（背景、スケール適用）
                pygame.draw.circle(screen, (255, 20, 147, int(180 * self.spawn_scale)), (center_x, center_y), circle_radius)
                
                # 元の画像を上に描画
                screen.blit(scaled_image, (draw_x, draw_y))
        else:
            # フォールバック: 従来の図形描画（スケール適用）
            if self.type == "heal":
                r = int(self.size * self.spawn_scale)
                cx, cy = r*2, r*2

                # 十字をやや立体的に描画
                surf = pygame.Surface((r*4, r*4), pygame.SRCALPHA)
                # 背景小円
                pygame.draw.circle(surf, (0, 100, 0, int(60 * self.spawn_scale)), (cx, cy), r+6)
                # 十字本体（影）
                pygame.draw.line(surf, (0, 120, 0), (cx - 8, cy + 1), (cx + 8, cy + 1), max(1, int(6 * self.spawn_scale)))
                pygame.draw.line(surf, (0, 120, 0), (cx + 1, cy - 8), (cx + 1, cy + 8), max(1, int(6 * self.spawn_scale)))
                # 十字ハイライト
                pygame.draw.line(surf, GREEN, (cx - 8, cy - 1), (cx + 8, cy - 1), max(1, int(4 * self.spawn_scale)))
                pygame.draw.line(surf, GREEN, (cx - 1, cy - 8), (cx - 1, cy + 8), max(1, int(4 * self.spawn_scale)))
                screen.blit(surf, (int(self.x - cx - camera_x), int(self.y - cy - camera_y)))
            elif self.type == "bomb":
                r = int(self.size * self.spawn_scale)
                surf = pygame.Surface((r*4, r*4), pygame.SRCALPHA)
                cx, cy = r*2, r*2
                base = RED
                darker = tuple(max(0, int(c * 0.5)) for c in base)
                highlight = tuple(min(255, int(c * 1.4)) for c in base)
                pygame.draw.circle(surf, darker + (230,), (cx, cy), r+6)
                pygame.draw.circle(surf, base + (240,), (int(cx - r*0.4), int(cy - r*0.4)), r)
                pygame.draw.circle(surf, highlight + (160,), (int(cx - r*0.8), int(cy - r*0.8)), int(r*0.4))
                pygame.draw.line(surf, YELLOW, (cx + r, cy - r), (cx + r + 6, cy - r - 6), 3)
                screen.blit(surf, (int(self.x - cx - camera_x), int(self.y - cy - camera_y)))
            elif self.type == "magnet":
                r = self.size
                surf = pygame.Surface((r*4, r*4), pygame.SRCALPHA)
                cx, cy = r*2, r*2
                
                # マグネットの U字形を描画
                # 背景グロー
                pygame.draw.circle(surf, (0, 100, 255, 60), (cx, cy), r+6)
                
                # U字の外側（影）
                pygame.draw.arc(surf, (0, 0, 100), (cx-r, cy-r, r*2, r*2), 0, math.pi, 6)
                pygame.draw.line(surf, (0, 0, 100), (cx-r+1, cy+1), (cx-r+1, cy+r+1), 6)
                pygame.draw.line(surf, (0, 0, 100), (cx+r-1, cy+1), (cx+r-1, cy+r+1), 6)
                
                # U字の本体
                pygame.draw.arc(surf, BLUE, (cx-r, cy-r, r*2, r*2), 0, math.pi, 4)
                pygame.draw.line(surf, BLUE, (cx-r, cy), (cx-r, cy+r), 4)
                pygame.draw.line(surf, BLUE, (cx+r, cy), (cx+r, cy+r), 4)
                
                # ハイライト
                pygame.draw.arc(surf, CYAN, (cx-r+2, cy-r+2, r*2-4, r*2-4), 0, math.pi, 2)
                
                screen.blit(surf, (int(self.x - cx - camera_x), int(self.y - cy - camera_y)))

class MoneyItem:
    """お金アイテムクラス"""
    def __init__(self, x, y, amount=None, box_type=None):
        self.x = x
        self.y = y
        self.size = 10
        self.speed = 3
        self.type = "money"
        self.collected = False
        
        # 出現アニメーション用
        self.spawn_time = pygame.time.get_ticks()
        self.spawn_scale = 0.0  # 開始時はサイズ0
        self.spawn_duration = 300  # 出現アニメーション時間（ミリ秒）
        
        # お金の量を設定
        if amount is None:
            if box_type is not None:
                self.amount = self._generate_amount_by_box_type(box_type)
            else:
                self.amount = self._generate_random_amount()
        else:
            self.amount = max(1, int(amount))
        
        # 金額に基づいてアイコンを決定
        self.money_type = self._get_money_type_by_amount(self.amount)
        
        # アイテム画像を読み込む
        try:
            icons = load_icons(size=32, icon_names=[self.money_type])
            self.image = icons.get(self.money_type)
        except Exception:
            self.image = None
        
        # アニメーション用
        self.animation_time = 0
        self.bob_offset = 0

    def _generate_amount_by_box_type(self, box_type):
        """ボックスタイプに基づいて金額を生成"""
        rand = random.random()
        
        if box_type == 1:
            # Box1: money1～4
            if rand < BOX1_MONEY1_RATE:
                return random.randint(MONEY1_AMOUNT_MIN, MONEY1_AMOUNT_MAX)
            elif rand < BOX1_MONEY1_RATE + BOX1_MONEY2_RATE:
                return random.randint(MONEY2_AMOUNT_MIN, MONEY2_AMOUNT_MAX)
            elif rand < BOX1_MONEY1_RATE + BOX1_MONEY2_RATE + BOX1_MONEY3_RATE:
                return random.randint(MONEY3_AMOUNT_MIN, MONEY3_AMOUNT_MAX)
            else:
                return random.randint(MONEY4_AMOUNT_MIN, MONEY4_AMOUNT_MAX)
        elif box_type == 2:
            # Box2: money3～5
            if rand < BOX2_MONEY3_RATE:
                return random.randint(MONEY3_AMOUNT_MIN, MONEY3_AMOUNT_MAX)
            elif rand < BOX2_MONEY3_RATE + BOX2_MONEY4_RATE:
                return random.randint(MONEY4_AMOUNT_MIN, MONEY4_AMOUNT_MAX)
            else:
                return random.randint(MONEY5_AMOUNT_MIN, MONEY5_AMOUNT_MAX)
        elif box_type == 3:
            # Box3: money4～5 (最高額寄り)
            if rand < BOX3_MONEY4_RATE:
                return random.randint(MONEY4_AMOUNT_MIN, MONEY4_AMOUNT_MAX)
            else:
                return random.randint(MONEY5_AMOUNT_MIN, MONEY5_AMOUNT_MAX)
        else:
            # デフォルト（従来のランダムシステム）
            return self._generate_random_amount()

    def _generate_random_amount(self):
        """新しい確率システムで金額を生成"""
        rand = random.random()
        
        if rand < MONEY1_DROP_RATE:
            return random.randint(MONEY1_AMOUNT_MIN, MONEY1_AMOUNT_MAX)
        elif rand < MONEY1_DROP_RATE + MONEY2_DROP_RATE:
            return random.randint(MONEY2_AMOUNT_MIN, MONEY2_AMOUNT_MAX)
        elif rand < MONEY1_DROP_RATE + MONEY2_DROP_RATE + MONEY3_DROP_RATE:
            return random.randint(MONEY3_AMOUNT_MIN, MONEY3_AMOUNT_MAX)
        elif rand < MONEY1_DROP_RATE + MONEY2_DROP_RATE + MONEY3_DROP_RATE + MONEY4_DROP_RATE:
            return random.randint(MONEY4_AMOUNT_MIN, MONEY4_AMOUNT_MAX)
        else:
            return random.randint(MONEY5_AMOUNT_MIN, MONEY5_AMOUNT_MAX)

    def _get_money_type_by_amount(self, amount):
        """金額に基づいてアイコンタイプを決定"""
        if amount <= 10:
            return "money1"
        elif amount <= 50:
            return "money2"
        elif amount <= 200:
            return "money3"
        elif amount <= 1000:
            return "money4"
        else:
            return "money5"

    def move_to_player(self, player):
        dx = player.x - self.x
        dy = player.y - self.y
        distance = math.sqrt(dx**2 + dy**2)
        
        # アイテムの引き寄せも同様にサブアイテムで拡張
        try:
            extra = float(player.get_gem_pickup_range()) if hasattr(player, 'get_gem_pickup_range') else 0.0
        except Exception:
            extra = 0.0
        attract_threshold = 120.0 + extra  # お金は少し広い範囲から引き寄せ

        # マグネット効果が有効な場合、全画面からの引き寄せ＋速度アップ
        if hasattr(player, 'is_magnet_active') and player.is_magnet_active():
            attract_threshold = float('inf')  # 距離制限なし
            speed_multiplier = MAGNET_FORCE_MULTIPLIER
        else:
            speed_multiplier = 1.0

        if distance < attract_threshold and distance != 0:
            move_speed = self.speed * speed_multiplier
            self.x += (dx / distance) * move_speed
            self.y += (dy / distance) * move_speed

    def draw(self, screen, camera_x=0, camera_y=0):
        # 出現アニメーションのスケール計算
        current_time = pygame.time.get_ticks()
        time_since_spawn = current_time - self.spawn_time
        
        if time_since_spawn < self.spawn_duration:
            # 出現アニメーション中：0から1にスケール
            progress = time_since_spawn / self.spawn_duration
            self.spawn_scale = min(1.0, progress * 1.2)  # 少しオーバーシュート
        else:
            self.spawn_scale = 1.0
        
        # スケールが0の場合は描画しない
        if self.spawn_scale <= 0:
            return
            
        # アニメーション更新
        self.animation_time += 0.1
        self.bob_offset = math.sin(self.animation_time) * 2  # 上下にふわふわ
        
        display_y = self.y + self.bob_offset
        
        # 画像が読み込まれている場合は画像を使用
        if self.image:
            # 画像のサイズに基づいて描画位置を調整（スケール適用）
            img_w, img_h = self.image.get_size()
            scaled_w = int(img_w * self.spawn_scale)
            scaled_h = int(img_h * self.spawn_scale)
            
            # スケールされた画像を作成
            if scaled_w > 0 and scaled_h > 0:
                scaled_image = pygame.transform.scale(self.image, (scaled_w, scaled_h))
                draw_x = int(self.x - scaled_w // 2 - camera_x)
                draw_y = int(display_y - scaled_h // 2 - camera_y)
                
                # 画像の中心座標
                center_x = int(self.x - camera_x)
                center_y = int(display_y - camera_y)
                
                # お金タイプに応じてグローの色を変更
                glow_colors = {
                    "money1": (255, 215, 0),    # 金色
                    "money2": (255, 255, 150),  # 明るい金色
                    "money3": (255, 165, 0),    # オレンジ金色
                    "money4": (255, 69, 0),     # 赤みがかった金色
                    "money5": (138, 43, 226)    # 紫色（レア感）
                }
                glow_color = glow_colors.get(self.money_type, (255, 215, 0))
                
                # 金色の円の半径（スケール適用）
                circle_radius = int(max(scaled_w, scaled_h) * 0.3)
                
                # グロー効果（複数の円を重ねて描画）
                for i in range(4):
                    glow_radius = circle_radius + (i + 1) * 2
                    glow_alpha = max(10, int((35 - i * 8) * self.spawn_scale))
                    glow_surf = pygame.Surface((glow_radius * 2 + 10, glow_radius * 2 + 10), pygame.SRCALPHA)
                    pygame.draw.circle(glow_surf, glow_color + (glow_alpha,), 
                                     (glow_radius + 5, glow_radius + 5), glow_radius)
                    screen.blit(glow_surf, (center_x - glow_radius - 5, center_y - glow_radius - 5))
                
                # メインの色の円（背景、スケール適用）
                pygame.draw.circle(screen, glow_color + (int(160 * self.spawn_scale),), (center_x, center_y), circle_radius)
                
                # 元の画像を上に描画
                screen.blit(scaled_image, (draw_x, draw_y))
                
                # 金額表示（小さなテキスト、スケール適用）
                try:
                    from resources import get_font
                    font = get_font(max(10, int(14 * self.spawn_scale)))
                    if font:
                        text = f"{self.amount}G"
                        text_surf = font.render(text, True, WHITE)
                        text_w = text_surf.get_width()
                        screen.blit(text_surf, (center_x - text_w // 2, center_y + circle_radius + 2))
                except Exception:
                    pass
        else:
            # フォールバック: 金貨風の円を描画
            r = self.size
            cx, cy = int(self.x - camera_x), int(display_y - camera_y)
            
            # 金色のコイン風描画
            gold_color = (255, 215, 0)
            dark_gold = (200, 165, 0)
            light_gold = (255, 255, 150)
            
            # 影
            pygame.draw.circle(screen, (100, 80, 0), (cx + 2, cy + 2), r + 2)
            # メインの金色
            pygame.draw.circle(screen, gold_color, (cx, cy), r)
            # ハイライト
            pygame.draw.circle(screen, light_gold, (cx - r//3, cy - r//3), r//2)
            # 輪郭
            pygame.draw.circle(screen, dark_gold, (cx, cy), r, 2)
            
            # 金額表示
            try:
                from resources import get_font
                font = get_font(12)
                if font:
                    text = f"{self.amount}"
                    text_surf = font.render(text, True, BLACK)
                    text_w, text_h = text_surf.get_size()
                    screen.blit(text_surf, (cx - text_w // 2, cy - text_h // 2))
            except Exception:
                pass