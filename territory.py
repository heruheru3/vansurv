import pygame
import random
import math
from constants import *

class Territory:
    """陣取りゲームの拠点を表現するクラス"""
    
    TERRITORY_TYPES = {
        'village': {'name': '村', 'defense': 50, 'income': 5, 'color': (139, 69, 19), 'size': 40},
        'town': {'name': '町', 'defense': 100, 'income': 10, 'color': (105, 105, 105), 'size': 50},
        'castle': {'name': '城', 'defense': 200, 'income': 20, 'color': (128, 128, 128), 'size': 60}
    }
    
    def __init__(self, x, y, territory_type='village', owner=None):
        self.x = x
        self.y = y
        self.territory_type = territory_type
        self.owner = owner  # None, 'player', 'ai_red', 'ai_blue', etc.
        self.original_owner = owner
        
        # 拠点の属性
        type_data = self.TERRITORY_TYPES[territory_type]
        self.max_defense = type_data['defense']
        self.current_defense = self.max_defense
        self.income = type_data['income']
        self.color = type_data['color']
        self.size = type_data['size']
        
        # 制圧関連
        self.under_siege = False
        self.siege_progress = 0.0
        self.siege_time_required = 5.0  # 5秒で制圧
        self.last_income_time = 0
        
        # 視覚効果
        self.pulse_timer = 0
        
    def update(self, dt):
        """拠点の状態更新"""
        self.pulse_timer += dt
        
        # 収入の生成（1秒ごと）
        current_time = pygame.time.get_ticks()
        if current_time - self.last_income_time >= 1000:
            self.last_income_time = current_time
            return self.income if self.owner == 'player' else 0
        return 0
        
    def start_siege(self):
        """制圧開始"""
        self.under_siege = True
        self.siege_progress = 0.0
        
    def update_siege(self, dt, player_nearby=False):
        """制圧進行状況の更新"""
        if not self.under_siege:
            return False
            
        if player_nearby:
            self.siege_progress += dt / self.siege_time_required
            if self.siege_progress >= 1.0:
                # 制圧完了
                self.owner = 'player'
                self.under_siege = False
                self.siege_progress = 0.0
                self.current_defense = self.max_defense
                return True
        else:
            # プレイヤーが離れると制圧進行が停止
            self.siege_progress = max(0.0, self.siege_progress - dt / (self.siege_time_required * 2))
            if self.siege_progress <= 0.0:
                self.under_siege = False
                
        return False
        
    def draw(self, screen, camera_x=0, camera_y=0):
        """拠点の描画"""
        screen_x = int(self.x - camera_x)
        screen_y = int(self.y - camera_y)
        
        # 画面外なら描画しない
        if (screen_x < -self.size or screen_x > SCREEN_WIDTH + self.size or 
            screen_y < -self.size or screen_y > SCREEN_HEIGHT + self.size):
            return
            
        # 拠点の基本色を決定
        if self.owner == 'player':
            base_color = (50, 150, 50)  # 緑
        elif self.owner == 'ai_red':
            base_color = (150, 50, 50)  # 赤
        elif self.owner == 'ai_blue':
            base_color = (50, 50, 150)  # 青
        else:
            base_color = self.color  # 中立
            
        # パルス効果
        pulse = abs(math.sin(self.pulse_timer * 2)) * 0.3 + 0.7
        display_color = tuple(int(c * pulse) for c in base_color)
        
        # 拠点本体の描画
        pygame.draw.circle(screen, display_color, (screen_x, screen_y), self.size)
        pygame.draw.circle(screen, WHITE, (screen_x, screen_y), self.size, 3)
        
        # 制圧進行状況の表示
        if self.under_siege:
            # 制圧ゲージの背景
            gauge_width = self.size * 2
            gauge_height = 8
            gauge_x = screen_x - gauge_width // 2
            gauge_y = screen_y - self.size - 15
            
            pygame.draw.rect(screen, BLACK, (gauge_x, gauge_y, gauge_width, gauge_height))
            pygame.draw.rect(screen, WHITE, (gauge_x, gauge_y, gauge_width, gauge_height), 1)
            
            # 制圧進行バー
            if self.siege_progress > 0:
                progress_width = int(gauge_width * self.siege_progress)
                pygame.draw.rect(screen, (255, 255, 0), (gauge_x, gauge_y, progress_width, gauge_height))
                
        # 拠点タイプの文字表示
        if hasattr(pygame.font, 'Font'):
            try:
                font = pygame.font.SysFont(None, 20)
                text = font.render(self.TERRITORY_TYPES[self.territory_type]['name'], True, WHITE)
                text_rect = text.get_rect(center=(screen_x, screen_y + self.size + 20))
                screen.blit(text, text_rect)
            except:
                pass
                
    def get_distance_to(self, x, y):
        """指定座標との距離を計算"""
        import math
        return math.sqrt((self.x - x) ** 2 + (self.y - y) ** 2)
        
    def is_player_nearby(self, player_x, player_y, threshold=80):
        """プレイヤーが近くにいるかチェック"""
        return self.get_distance_to(player_x, player_y) <= threshold


class TerritoryManager:
    """拠点群を管理するクラス"""
    
    def __init__(self):
        self.territories = []
        self.player_resources = {'gold': 100, 'income': 0}
        
    def generate_territories(self, count=12):
        """ランダムに拠点を生成"""
        self.territories.clear()
        
        # マップサイズの範囲内でランダム配置
        margin = 200
        for i in range(count):
            x = random.randint(margin, WORLD_WIDTH - margin)
            y = random.randint(margin, WORLD_HEIGHT - margin)
            
            # 拠点タイプをランダムに決定（村が多め）
            territory_type = random.choices(
                ['village', 'town', 'castle'],
                weights=[60, 30, 10]
            )[0]
            
            # AI勢力をランダムに割り当て（一部は中立）
            if i < count // 3:
                owner = None  # 中立
            elif i < count * 2 // 3:
                owner = 'ai_red'
            else:
                owner = 'ai_blue'
                
            territory = Territory(x, y, territory_type, owner)
            self.territories.append(territory)
            
    def update(self, dt, player):
        """全拠点の更新"""
        total_income = 0
        
        for territory in self.territories:
            # 拠点の基本更新
            income = territory.update(dt)
            total_income += income
            
            # 制圧処理
            if territory.owner != 'player':
                player_nearby = territory.is_player_nearby(player.x, player.y)
                
                if player_nearby and not territory.under_siege:
                    territory.start_siege()
                    
                if territory.update_siege(dt, player_nearby):
                    # 制圧完了時の処理
                    print(f"[INFO] {territory.TERRITORY_TYPES[territory.territory_type]['name']}を制圧しました！")
                    
        # プレイヤーの資源を更新
        self.player_resources['gold'] += total_income
        self.player_resources['income'] = sum(t.income for t in self.territories if t.owner == 'player')
        
    def draw(self, screen, camera_x=0, camera_y=0):
        """全拠点の描画"""
        for territory in self.territories:
            territory.draw(screen, camera_x, camera_y)
            
    def get_player_territories(self):
        """プレイヤーが所有する拠点数を取得"""
        return len([t for t in self.territories if t.owner == 'player'])
        
    def get_total_territories(self):
        """総拠点数を取得"""
        return len(self.territories)
