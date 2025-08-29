# filepath: e:\jupy_work\vansurv\effects\items.py
import pygame
import math
from constants import *

class ExperienceGem:
    def __init__(self, x, y, value=1):
        self.x = x
        self.y = y
        self.size = 8
        self.speed = 3
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

        if distance < attract_threshold and distance != 0:
            self.x += (dx / distance) * self.speed
            self.y += (dy / distance) * self.speed

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
        # アイテム表示（heal/bomb）の陰影付け
        if self.type == "heal":
            # 十字をやや立体的に描画
            r = self.size
            surf = pygame.Surface((r*4, r*4), pygame.SRCALPHA)
            cx, cy = r*2, r*2
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