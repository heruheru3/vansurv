import pygame

class Weapon:
    def __init__(self):
        self.level = 1
        self.cooldown = 1000
        # 初期化時にすぐ攻撃できるよう、last_attack_time を cooldown の負値に設定
        self.last_attack_time = -self.cooldown
        # デフォルトダメージを控えめに調整（以前は10）
        self.damage = 5

    def can_attack(self):
        current_time = pygame.time.get_ticks()
        return current_time - self.last_attack_time >= self.cooldown

    def update_cooldown(self):
        self.last_attack_time = pygame.time.get_ticks()

    def get_upgrade_text(self):
        return f"Level {self.level} -> {self.level + 1}\nDamage: {self.damage:.1f} -> {self.damage * 1.2:.1f}"

    def level_up(self):
        """レベルアップ時の基本処理"""
        self.level += 1