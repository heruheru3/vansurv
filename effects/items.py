# filepath: e:\jupy_work\vansurv\effects\items.py
import pygame
import math
from constants import *
from resources import load_icons

class ExperienceGem:
    def __init__(self, x, y, value=1):
        self.x = x
        self.y = y
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
        # 画像が読み込まれている場合は画像を使用
        if self.image:
            # 画像のサイズに基づいて描画位置を調整
            img_w, img_h = self.image.get_size()
            draw_x = int(self.x - img_w // 2 - camera_x)
            draw_y = int(self.y - img_h // 2 - camera_y)
            
            # 画像の中心座標
            center_x = int(self.x - camera_x)
            center_y = int(self.y - camera_y)
            
            # ピンクの円の半径（画像サイズの約70%）
            circle_radius = int(max(img_w, img_h) * 0.35)
            
            # グロー効果（複数の円を重ねて描画）
            glow_color = (255, 20, 147, 30)  # DeepPink with low alpha
            for i in range(5):
                glow_radius = circle_radius + (i + 1) * 3
                glow_alpha = max(10, 40 - i * 8)
                glow_surf = pygame.Surface((glow_radius * 2 + 10, glow_radius * 2 + 10), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (255, 20, 147, glow_alpha), 
                                 (glow_radius + 5, glow_radius + 5), glow_radius)
                screen.blit(glow_surf, (center_x - glow_radius - 5, center_y - glow_radius - 5))
            
            # メインのピンクの円（背景）
            pygame.draw.circle(screen, (255, 20, 147, 180), (center_x, center_y), circle_radius)
            
            # 元の画像を上に描画
            screen.blit(self.image, (draw_x, draw_y))
        else:
            # フォールバック: 従来の図形描画
            if self.type == "heal":
                r = self.size
                cx, cy = r*2, r*2

                # 十字をやや立体的に描画
                surf = pygame.Surface((r*4, r*4), pygame.SRCALPHA)
                # 背景小円
                pygame.draw.circle(surf, (0, 100, 0, 60), (cx, cy), r+6)
                # 十字本体（影）
                pygame.draw.line(surf, (0, 120, 0), (cx - 8, cy + 1), (cx + 8, cy + 1), 6)
                pygame.draw.line(surf, (0, 120, 0), (cx + 1, cy - 8), (cx + 1, cy + 8), 6)
                # 十字ハイライト
                pygame.draw.line(surf, GREEN, (cx - 8, cy - 1), (cx + 8, cy - 1), 4)
                pygame.draw.line(surf, GREEN, (cx - 1, cy - 8), (cx - 1, cy + 8), 4)
                screen.blit(surf, (int(self.x - cx - camera_x), int(self.y - cy - camera_y)))
            elif self.type == "bomb":
                r = self.size
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