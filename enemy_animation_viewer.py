import pygame
import sys
import os
import math
from constants import *
from enemy import Enemy

class EnemyAnimationViewer:
    def __init__(self):
        pygame.init()
        
        # 画面設定（小さめの確認用ウィンドウ）
        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("エネミーアニメーション確認ツール")
        
        # 時計とFPS
        self.clock = pygame.time.Clock()
        self.fps = 60
        
        # ダミープレイヤー（敵の動きを確認するため）
        self.player = DummyPlayer(self.screen_width // 2, self.screen_height // 2)
        
        # 表示用敵リスト
        self.enemies = []
        self.spawn_enemies()
        
        # 表示設定
        self.scale = 4  # 4倍拡大表示
        self.background_color = (50, 50, 50)  # ダークグレー背景
        
        # UI設定（日本語対応フォント）
        self.font = self._get_japanese_font(24)
        self.info_font = self._get_japanese_font(18)
        
        # 表示切り替え
        self.show_info = True
    
    def _get_japanese_font(self, size):
        """日本語対応フォントを取得"""
        # 日本語フォント候補
        font_candidates = [
            "msgothic",      # MS ゴシック
            "meiryo",        # Meiryo
            "msmincho",      # MS 明朝
            "arial unicode ms",  # Arial Unicode MS
            "yugothic",      # Yu Gothic
            "arial",         # Arial (フォールバック)
            None            # システムデフォルト
        ]
        
        for font_name in font_candidates:
            try:
                if font_name:
                    font = pygame.font.SysFont(font_name, size)
                else:
                    font = pygame.font.SysFont(None, size)
                
                # 日本語テスト文字でフォントをテスト
                test_surface = font.render("テスト", True, (255, 255, 255))
                if test_surface.get_width() > 0:
                    return font
            except:
                continue
        
        # 全て失敗した場合はデフォルトフォント
        return pygame.font.SysFont(None, size)
        
    def spawn_enemies(self):
        """表示用の敵を生成"""
        self.enemies.clear()
        
        # 各行動パターン・レベルの組み合わせで敵を配置
        start_x = 150
        start_y = 100
        spacing_x = 150
        spacing_y = 120
        
        for behavior_type in range(1, 5):  # 行動パターン1-4
            for enemy_level in range(1, 6):  # レベル1-5
                x = start_x + (enemy_level - 1) * spacing_x
                y = start_y + (behavior_type - 1) * spacing_y
                
                # ダミーの敵を作成
                enemy = Enemy(self.screen, 60, spawn_x=x, spawn_y=y)
                # 強制的に設定を変更
                enemy.behavior_type = behavior_type
                enemy.enemy_type = enemy_level
                enemy.setup_enemy_stats()
                
                # 移動を開始させるため、少し動かす
                enemy.last_x = x - 1
                enemy.last_y = y - 1
                enemy.is_moving = True
                
                self.enemies.append(enemy)
    
    def handle_events(self):
        """イベント処理"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_r:
                    # リスポーン
                    self.spawn_enemies()
                elif event.key == pygame.K_i:
                    # 情報表示切り替え
                    self.show_info = not self.show_info
                elif event.key == pygame.K_SPACE:
                    # アニメーション一時停止/再開
                    for enemy in self.enemies:
                        enemy.is_moving = not enemy.is_moving
        
        return True
    
    def update(self):
        """更新処理"""
        # 敵のアニメーション更新
        for enemy in self.enemies:
            # 円運動させて常に動いているようにする
            center_x = 150 + (enemy.enemy_type - 1) * 150
            center_y = 100 + (enemy.behavior_type - 1) * 120
            radius = 30
            time_factor = pygame.time.get_ticks() / 2000.0  # ゆっくりとした円運動
            
            enemy.x = center_x + math.cos(time_factor + enemy.enemy_type * 0.5) * radius
            enemy.y = center_y + math.sin(time_factor + enemy.enemy_type * 0.5) * radius
            
            # アニメーション更新
            enemy.move(self.player, enemies=self.enemies)
    
    def draw(self):
        """描画処理"""
        self.screen.fill(self.background_color)
        
        # 敵を描画
        for enemy in self.enemies:
            # カメラなしで直接描画（拡大表示）
            enemy.draw(self.screen, camera_x=0, camera_y=0)
        
        # 情報表示
        if self.show_info:
            self.draw_info()
        
        # 操作説明
        self.draw_controls()
        
        pygame.display.flip()
    
    def draw_info(self):
        """敵の情報を表示"""
        y_offset = 10
        
        # ヘッダー
        header_text = "行動パターン / レベル →"
        header_surface = self.font.render(header_text, True, (255, 255, 255))
        self.screen.blit(header_surface, (10, y_offset))
        
        # レベル番号を表示
        for level in range(1, 6):
            level_text = f"Lv{level}"
            level_surface = self.info_font.render(level_text, True, (255, 255, 255))
            x_pos = 150 + (level - 1) * 150 - 10
            self.screen.blit(level_surface, (x_pos, y_offset + 25))
        
        # 行動パターン名を表示
        behavior_names = {
            1: "追跡",
            2: "直進",
            3: "距離保持",
            4: "遅速追跡"
        }
        
        for behavior in range(1, 5):
            behavior_text = behavior_names[behavior]
            behavior_surface = self.info_font.render(behavior_text, True, (255, 255, 255))
            y_pos = 100 + (behavior - 1) * 120 - 30
            self.screen.blit(behavior_surface, (10, y_pos))
    
    def draw_controls(self):
        """操作説明を表示"""
        controls = [
            "R: リスポーン",
            "I: 情報表示切り替え",
            "SPACE: アニメーション一時停止/再開",
            "ESC: 終了"
        ]
        
        y_start = self.screen_height - len(controls) * 20 - 10
        
        for i, control in enumerate(controls):
            control_surface = self.info_font.render(control, True, (200, 200, 200))
            self.screen.blit(control_surface, (10, y_start + i * 20))
    
    def run(self):
        """メインループ"""
        running = True
        
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(self.fps)
        
        pygame.quit()
        sys.exit()


class DummyPlayer:
    """ダミープレイヤークラス（敵の動作確認用）"""
    def __init__(self, x, y):
        self.x = x
        self.y = y


def main():
    try:
        viewer = EnemyAnimationViewer()
        viewer.run()
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    main()
