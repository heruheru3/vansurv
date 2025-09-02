import pygame
import math
import random

class BattleEffect:
    """拠点間戦闘のエフェクト"""
    
    def __init__(self, start_x, start_y, end_x, end_y, attacker_color):
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = end_x
        self.end_y = end_y
        self.attacker_color = attacker_color
        
        self.lifetime = 60  # 1秒間表示
        self.max_lifetime = self.lifetime
        
        # 攻撃ラインのアニメーション
        self.line_progress = 0.0
        
        # 爆発エフェクト用パーティクル
        self.explosion_particles = []
        for _ in range(8):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 5)
            self.explosion_particles.append({
                'x': end_x,
                'y': end_y,
                'dx': math.cos(angle) * speed,
                'dy': math.sin(angle) * speed,
                'life': 30
            })
            
    def update(self):
        self.lifetime -= 1
        self.line_progress = min(1.0, (self.max_lifetime - self.lifetime) / 20.0)
        
        # パーティクルの更新
        for particle in self.explosion_particles:
            particle['x'] += particle['dx']
            particle['y'] += particle['dy']
            particle['life'] -= 1
            
        return self.lifetime > 0
        
    def draw(self, screen, camera_x=0, camera_y=0):
        if self.line_progress <= 0:
            return
            
        # 攻撃ライン
        start_screen_x = int(self.start_x - camera_x)
        start_screen_y = int(self.start_y - camera_y)
        
        # ラインの終点を進行度に合わせて調整
        line_end_x = self.start_x + (self.end_x - self.start_x) * self.line_progress
        line_end_y = self.start_y + (self.end_y - self.start_y) * self.line_progress
        
        end_screen_x = int(line_end_x - camera_x)
        end_screen_y = int(line_end_y - camera_y)
        
        # 攻撃ラインの描画
        if self.line_progress < 1.0:
            pygame.draw.line(screen, self.attacker_color, 
                           (start_screen_x, start_screen_y), 
                           (end_screen_x, end_screen_y), 3)
                           
        # 爆発パーティクル
        if self.line_progress >= 0.8:
            for particle in self.explosion_particles:
                if particle['life'] > 0:
                    px = int(particle['x'] - camera_x)
                    py = int(particle['y'] - camera_y)
                    pygame.draw.circle(screen, self.attacker_color[:3], (px, py), 3)
