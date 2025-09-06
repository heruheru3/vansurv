import pygame
import math
import random
from constants import *
from resources import get_font

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

class AvoidanceParticle:
    def __init__(self, x=0, y=0, size=20, duration=18):
        # プレイヤー位置とサイズを保持して、プレイヤー上部に青い半透明フラッシュを描く
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
        pygame.draw.circle(s, (0, 0, 255, alpha), (surf_size // 2, surf_size // 2), r)
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
                self.font = get_font(22)
            except Exception:
                try:
                    self.font = get_font(36)
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
            try:
                DamageNumber.font = get_font(18)
            except Exception:
                DamageNumber.font = pygame.font.SysFont(None, 18)

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


class LuckyText:
    """回避成功時にプレイヤー上部へ小さく表示するテキスト（短時間）。"""
    font = None

    def __init__(self, x, y, text="Lukey!", color=CYAN):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.duration = 20  # 短め
        self.timer = self.duration
        self.vy = -0.5
        if LuckyText.font is None:
            try:
                LuckyText.font = get_font(14)  # 小さめ
            except Exception:
                LuckyText.font = pygame.font.SysFont(None, 14)

    def update(self):
        self.y += self.vy
        self.timer -= 1
        return self.timer > 0

    def draw(self, screen, camera_x=0, camera_y=0):
        elapsed = self.duration - self.timer
        if elapsed < 4:
            alpha = int(255 * (elapsed / 4))
        elif self.timer < 6:
            alpha = int(255 * (self.timer / 6))
        else:
            alpha = 255
        alpha = max(0, min(255, alpha))

        text_surf = LuckyText.font.render(str(self.text), True, self.color)
        try:
            text_surf.set_alpha(alpha)
        except Exception:
            pass

        sx = int(self.x - camera_x)
        sy = int(self.y - camera_y)
        rect = text_surf.get_rect(center=(sx, sy))

        # ささやかなシャドウ
        try:
            shadow = LuckyText.font.render(str(self.text), True, (0, 0, 0))
            shadow.set_alpha(max(40, int(alpha * 0.6)))
            screen.blit(shadow, rect.move(1, 1))
        except Exception:
            pass
        screen.blit(text_surf, rect)


class HealEffect:
    """HP回復時のエフェクト"""
    def __init__(self, x, y, heal_amount=20):
        self.x = x
        self.y = y
        self.heal_amount = heal_amount
        self.timer = 80  # エフェクトの持続時間（フレーム）を少し長く
        self.font = get_font(18)  # フォントサイズを少し大きく
        self.initial_y = y
        
    def update(self):
        self.timer -= 1
        # 上に浮上する動き
        self.y -= 0.8
        return self.timer > 0
        
    def draw(self, screen, camera_x=0, camera_y=0):
        if self.timer <= 0:
            return
            
        # フェードアウト効果
        alpha = int(255 * (self.timer / 80))
        alpha = max(0, min(255, alpha))
        
        # 回復量を表示
        text = f"+{self.heal_amount} HP"
        color = (50, 255, 50)  # より明るい緑色
        
        text_surf = self.font.render(text, True, color)
        try:
            text_surf.set_alpha(alpha)
        except Exception:
            pass
        
        # 描画位置計算
        sx = int(self.x - camera_x)
        sy = int(self.y - camera_y)
        rect = text_surf.get_rect(center=(sx, sy))
        
        # より濃い影を描画
        try:
            shadow = self.font.render(text, True, (0, 0, 0))
            shadow.set_alpha(max(30, int(alpha * 0.5)))
            screen.blit(shadow, rect.move(2, 2))
        except Exception:
            pass
            
        # メインテキストを描画
        screen.blit(text_surf, rect)


class AutoHealEffect:
    """自動回復のエフェクト（プレイヤー周りに緑の輝き）"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.timer = 45  # エフェクトの持続時間
        self.max_radius = 25
        self.particles = []
        
        # 小さな緑のパーティクルを生成
        for _ in range(8):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1, 3)
            self.particles.append({
                'x': x + random.uniform(-10, 10),
                'y': y + random.uniform(-10, 10),
                'dx': math.cos(angle) * speed * 0.5,
                'dy': math.sin(angle) * speed * 0.5,
                'life': random.randint(30, 45)
            })
    
    def update(self):
        self.timer -= 1
        
        # パーティクルを更新
        for particle in self.particles[:]:
            particle['x'] += particle['dx']
            particle['y'] += particle['dy']
            particle['life'] -= 1
            if particle['life'] <= 0:
                self.particles.remove(particle)
                
        return self.timer > 0
        
    def draw(self, screen, camera_x=0, camera_y=0):
        if self.timer <= 0:
            return
            
        # メイン輝きの描画
        progress = 1 - (self.timer / 45)
        radius = int(self.max_radius * (0.5 + 0.5 * math.sin(progress * math.pi)))
        alpha = int(80 * (self.timer / 45))
        
        # 緑の輝く円を描画
        sx = int(self.x - camera_x)
        sy = int(self.y - camera_y)
        
        if radius > 0:
            # 外側の薄い円
            try:
                heal_surface = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
                pygame.draw.circle(heal_surface, (0, 255, 0, alpha // 3), 
                                 (radius * 2, radius * 2), radius * 2)
                pygame.draw.circle(heal_surface, (0, 255, 0, alpha // 2), 
                                 (radius * 2, radius * 2), radius)
                screen.blit(heal_surface, (sx - radius * 2, sy - radius * 2))
            except Exception:
                # フォールバック：通常の円描画
                pygame.draw.circle(screen, (0, 255, 0), (sx, sy), radius, 2)
        
        # 小さなパーティクルを描画
        for particle in self.particles:
            p_alpha = int(255 * (particle['life'] / 45))
            if p_alpha > 0:
                px = int(particle['x'] - camera_x)
                py = int(particle['y'] - camera_y)
                pygame.draw.circle(screen, (100, 255, 100), (px, py), 2)


class BossDeathEffect:
    """ボス死亡時のFinal Fantasy風赤いドットエフェクト"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.timer = 120  # 2秒間（60FPS想定で120フレーム）
        self.particles = []
        
        # 赤いドットを放射状に生成
        num_particles = 40
        for i in range(num_particles):
            angle = (2 * math.pi * i) / num_particles
            distance = random.uniform(10, 50)
            speed = random.uniform(1, 3)
            
            self.particles.append({
                'x': x + math.cos(angle) * distance,
                'y': y + math.sin(angle) * distance,
                'dx': math.cos(angle) * speed,
                'dy': math.sin(angle) * speed,
                'life': random.randint(60, 120),  # 各パーティクルの寿命
                'size': random.uniform(2, 4)
            })
    
    def update(self):
        self.timer -= 1
        
        # パーティクルを更新
        for particle in self.particles[:]:
            particle['x'] += particle['dx']
            particle['y'] += particle['dy']
            particle['life'] -= 1
            if particle['life'] <= 0:
                self.particles.remove(particle)
                
        return self.timer > 0
        
    def draw(self, screen, camera_x=0, camera_y=0):
        if self.timer <= 0:
            return
            
        # 各パーティクルを描画
        for particle in self.particles:
            # 寿命に応じてアルファを変化
            alpha = int(255 * (particle['life'] / 120))
            alpha = max(0, min(255, alpha))
            
            # 赤いドットを描画
            color = (120, 20, 255, alpha)
            px = int(particle['x'] - camera_x)
            py = int(particle['y'] - camera_y)
            
            # 半透明サーフェスを使って描画
            size = int(particle['size'])
            if size > 0:
                try:
                    dot_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                    pygame.draw.circle(dot_surface, color, (size, size), size)
                    screen.blit(dot_surface, (px - size, py - size))
                except Exception:
                    # フォールバック：通常の円描画
                    pygame.draw.circle(screen, (255, 0, 0), (px, py), size)