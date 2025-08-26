import pygame
import math
import random
from constants import *

class DeathParticle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.speed = random.uniform(2, 5)
        self.angle = math.radians(random.uniform(0, 360))
        self.lifetime = 30  # フレーム数
        self.size = random.randint(2, 4)
        self.dx = math.cos(self.angle) * self.speed
        self.dy = math.sin(self.angle) * self.speed

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.lifetime -= 1
        self.size = max(0, self.size - 0.1)
        return self.lifetime > 0

    def draw(self, screen, camera_x=0, camera_y=0):
        pygame.draw.circle(screen, self.color, 
                         (int(self.x - camera_x), int(self.y - camera_y)), 
                         int(self.size))

class PlayerHurtParticle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = random.uniform(2, 5)
        self.angle = math.radians(random.uniform(0, 360))
        self.lifetime = 20
        self.size = random.randint(2, 4)
        self.dx = math.cos(self.angle) * self.speed
        self.dy = math.sin(self.angle) * self.speed
        self.color = (255, 100, 100)

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.lifetime -= 1
        self.size = max(0, self.size - 0.12)
        return self.lifetime > 0

    def draw(self, screen, camera_x=0, camera_y=0):
        pygame.draw.circle(screen, self.color, (int(self.x - camera_x), int(self.y - camera_y)), int(self.size))

class HurtFlash:
    def __init__(self, x=0, y=0, size=20, duration=12):
        # プレイヤー位置とサイズを保持して、プレイヤー上部に赤い半透明フラッシュを描く
        self.x = x
        self.y = y
        self.size = max(8, int(size))
        self.duration = duration
        self.timer = duration

    def update(self):
        self.timer -= 1
        return self.timer > 0

    def draw(self, screen, camera_x=0, camera_y=0):
        # プレイヤー位置に半透明の赤い円を描画（カメラオフセットを適用）
        alpha = int(150 * (self.timer / max(1, self.duration)))
        r = int(self.size * (1.0 + 0.25 * (self.timer / max(1, self.duration))))
        surf_size = r * 2 + 4
        s = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        # 円を描画してからスクリーンにブリット
        pygame.draw.circle(s, (255, 0, 0, alpha), (surf_size // 2, surf_size // 2), r)
        screen.blit(s, (int(self.x - camera_x - surf_size // 2), int(self.y - camera_y - surf_size // 2)))


class LevelUpEffect:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        # 表示を短めにして、プレイヤー上に文字を出す用途に変更
        self.duration = 48
        self.timer = self.duration
        # 色とフォントなどはここで初期化
        self.color = (255, 220, 120)
        self.font = None

    def update(self):
        self.timer -= 1
        return self.timer > 0

    def draw(self, screen, camera_x=0, camera_y=0):
        # プレイヤー上部に "LEVEL UP!" の文字を表示する
        if self.font is None:
            try:
                # 少し小さめに調整
                self.font = pygame.font.Font(None, 36)
            except Exception:
                self.font = pygame.font.SysFont(None, 36)

        # フェードイン・アウトのアルファ
        elapsed = self.duration - self.timer
        if elapsed < 8:
            alpha = int(255 * (elapsed / 8))
        elif self.timer < 12:
            alpha = int(255 * (self.timer / 12))
        else:
            alpha = 255
        alpha = max(0, min(255, alpha))

        text_surf = self.font.render("LEVEL UP!", True, self.color)
        try:
            text_surf.set_alpha(alpha)
        except Exception:
            pass

        # 若干上に表示
        sx = int(self.x - camera_x)
        sy = int(self.y - camera_y) - (self.size if hasattr(self, 'size') else 40)
        rect = text_surf.get_rect(center=(sx, sy))

        # ドロップシャドウ
        shadow = self.font.render("LEVEL UP!", True, (0, 0, 0))
        try:
            shadow.set_alpha(max(40, int(alpha * 0.6)))
        except Exception:
            pass
        shadow_rect = shadow.get_rect(center=(sx + 2, sy + 2))
        screen.blit(shadow, shadow_rect)
        screen.blit(text_surf, rect)

class SpawnParticle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.timer = 18
        self.size = random.randint(3, 6)
        self.dx = random.uniform(-1.5, 1.5)
        self.dy = random.uniform(-1.5, 1.5)

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.timer -= 1
        self.size = max(0, self.size - 0.15)
        return self.timer > 0

    def draw(self, screen, camera_x=0, camera_y=0):
        pygame.draw.circle(screen, self.color, (int(self.x - camera_x), int(self.y - camera_y)), int(self.size))

class DamageNumber:
    """敵の上に一時的に表示されるダメージ数。素早くフェードイン・フェードアウトする."""
    font = None

    def __init__(self, x, y, amount, color=WHITE):
        self.x = x
        self.y = y
        self.amount = amount
        self.color = color
        self.duration = 24  # 総フレーム数
        self.timer = self.duration
        self.vy = -0.8  # 上方向に少し移動
        self.fade_in = 4
        self.fade_out = 6
        if DamageNumber.font is None:
            # ダメージ表示はやや大きめに調整
            DamageNumber.font = pygame.font.Font(None, 26)

    def update(self):
        # 上に移動しつつタイマーを減らす
        self.y += self.vy
        self.timer -= 1
        return self.timer > 0

    def draw(self, screen, camera_x=0, camera_y=0):
        # アルファ計算（フェードイン→表示→フェードアウト）
        elapsed = self.duration - self.timer
        if elapsed < self.fade_in:
            alpha = int(255 * (elapsed / max(1, self.fade_in)))
        elif self.timer < self.fade_out:
            alpha = int(255 * (self.timer / max(1, self.fade_out)))
        else:
            alpha = 255

        # テキストを描画（中央揃え）
        text_surf = DamageNumber.font.render(str(self.amount), True, self.color)
        # サーフェスにアルファを適用してからブリット
        try:
            text_surf.set_alpha(alpha)
        except Exception:
            pass
        screen.blit(text_surf, (int(self.x - text_surf.get_width() / 2 - camera_x), int(self.y - text_surf.get_height() / 2 - camera_y)))