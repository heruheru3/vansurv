import pygame
import random
import math
from constants import *

class Enemy:
    def __init__(self, screen, game_time, spawn_x=None, spawn_y=None, spawn_side=None):
        self.screen = screen
        self.size = 15
        # ヒット時のフラッシュ用タイマ（秒）
        self.hit_flash_timer = 0.0
        self.hit_flash_duration = 0.25  # フェードイン+フェードアウトの合計時間
        
        # 全体的にやや遅めに調整
        # base_speed を導入して、プレイヤーの speed 変更の影響を受けないようにする
        self.base_speed = 1.5
        self.speed = self.base_speed
        
        # 敵の種類をランダムに決定（game_timeに応じて変化）
        self.enemy_type = self.get_random_enemy_type(game_time)
        
        # 敵のタイプに応じてステータスを設定
        self.setup_enemy_stats()
        
        # スポーン位置の指定があればそれを使う（main からカメラ外座標を渡せる）
        if spawn_x is not None and spawn_y is not None:
            # 明示的なワールド座標を使用
            self.x = spawn_x
            self.y = spawn_y
        else:
            # ランダムな位置に出現（ワールド外から）
            side = spawn_side if spawn_side is not None else random.randint(0, 3)
            margin = 20
            if side == 0:  # 上
                self.x = random.randint(0, WORLD_WIDTH)
                self.y = -margin
            elif side == 1:  # 右
                self.x = WORLD_WIDTH + margin
                self.y = random.randint(0, WORLD_HEIGHT)
            elif side == 2:  # 下
                self.x = random.randint(0, WORLD_WIDTH)
                self.y = WORLD_HEIGHT + margin
            else:  # 左
                self.x = -margin
                self.y = random.randint(0, WORLD_HEIGHT)

    def get_random_enemy_type(self, game_time):
        # 時間に応じて出現する敵のタイプを制限
        if game_time <= 30:  # 序盤（0-30秒）
            rand = random.random()
            if rand < 0.7:    # 70%
                return 1      # 最弱
            else:            # 30%
                return 2      # 弱
        elif game_time <= 70:  # 中盤（31-70秒）
            rand = random.random()
            if rand < 0.3:    # 30%
                return 1      # 最弱
            elif rand < 0.6:  # 30%
                return 2      # 弱
            elif rand < 0.85: # 25%
                return 3      # 中
            else:            # 15%
                return 4      # 強
        else:                # 終盤（71秒以降）
            rand = random.random()
            if rand < 0.3:    # 30%
                return 3      # 中
            elif rand < 0.6:  # 30%
                return 4      # 強
            else:            # 40%
                return 5      # 最強

    def setup_enemy_stats(self):
        # タイプに応じてステータスを設定（速度を全体的に約25%低下させる）
        if self.enemy_type == 1:
            self.hp = 10
            self.base_speed = 1.125
            self.speed = self.base_speed
            self.color = (255, 150, 150)  # 薄い赤
            self.damage = 2
        elif self.enemy_type == 2:
            self.hp = 20
            self.base_speed = 1.5
            self.speed = self.base_speed
            self.color = (255, 100, 100)  # やや薄い赤
            self.damage = 4
        elif self.enemy_type == 3:
            self.hp = 30
            self.base_speed = 1.875
            self.speed = self.base_speed
            self.color = (255, 50, 50)    # 普通の赤
            self.damage = 5
        elif self.enemy_type == 4:
            self.hp = 40
            self.base_speed = 2.0
            self.speed = self.base_speed
            self.color = (200, 0, 0)      # 濃い赤
            self.damage = 6
        else:  # type 5
            self.hp = 50
            self.base_speed = 2.25
            self.speed = self.base_speed
            self.color = (150, 0, 0)      # 最も濃い赤
            self.damage = 8

    def move(self, player):
        angle = math.atan2(player.y - self.y, player.x - self.x)
        
        # 新しい位置を計算
        new_x = self.x + math.cos(angle) * self.base_speed
        new_y = self.y + math.sin(angle) * self.base_speed
        
        # 障害物との衝突判定（マップが有効な場合のみ）
        if USE_STAGE_MAP:
            try:
                from stage import get_stage_map
                stage_map = get_stage_map()
                
                # 敵の四隅をチェック
                corners = [
                    (new_x - self.size//2, new_y - self.size//2),
                    (new_x + self.size//2, new_y - self.size//2),
                    (new_x - self.size//2, new_y + self.size//2),
                    (new_x + self.size//2, new_y + self.size//2),
                ]
                
                # 障害物にぶつからない場合のみ移動
                collision = False
                for corner_x, corner_y in corners:
                    if stage_map.is_obstacle_at_world_pos(corner_x, corner_y):
                        collision = True
                        break
                
                if not collision:
                    self.x = new_x
                    self.y = new_y
                else:
                    # 障害物がある場合は X軸かY軸のみの移動を試す
                    x_only_corners = [
                        (new_x - self.size//2, self.y - self.size//2),
                        (new_x + self.size//2, self.y - self.size//2),
                        (new_x - self.size//2, self.y + self.size//2),
                        (new_x + self.size//2, self.y + self.size//2),
                    ]
                    
                    y_only_corners = [
                        (self.x - self.size//2, new_y - self.size//2),
                        (self.x + self.size//2, new_y - self.size//2),
                        (self.x - self.size//2, new_y + self.size//2),
                        (self.x + self.size//2, new_y + self.size//2),
                    ]
                    
                    # X軸のみの移動を試す
                    x_collision = False
                    for corner_x, corner_y in x_only_corners:
                        if stage_map.is_obstacle_at_world_pos(corner_x, corner_y):
                            x_collision = True
                            break
                    
                    if not x_collision:
                        self.x = new_x
                    else:
                        # Y軸のみの移動を試す
                        y_collision = False
                        for corner_x, corner_y in y_only_corners:
                            if stage_map.is_obstacle_at_world_pos(corner_x, corner_y):
                                y_collision = True
                                break
                        
                        if not y_collision:
                            self.y = new_y
            
            except Exception:
                # 障害物判定に失敗した場合は通常の移動
                self.x = new_x
                self.y = new_y
        else:
            # マップが無効な場合は障害物判定なしで移動
            self.x = new_x
            self.y = new_y

        # ヒットフラッシュのタイマを減算（フレーム毎に呼ばれることを想定、60FPS基準）
        if self.hit_flash_timer > 0.0:
            self.hit_flash_timer = max(0.0, self.hit_flash_timer - (1.0/60.0))

    def draw(self, screen, camera_x=0, camera_y=0):
        # ワールド座標からスクリーン座標に変換
        sx = int(self.x - camera_x)
        sy = int(self.y - camera_y)

        # 陰影付きの円で描画（色は self.color をベースに調整）
        r = self.size
        surf = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        base = self.color
        darker = tuple(max(0, int(c * 0.45)) for c in base)
        mid = tuple(max(0, int(c * 0.95)) for c in base)
        highlight = tuple(min(255, int(c * 1.3)) for c in base)
        # 影のレイヤー
        pygame.draw.circle(surf, darker + (240,), (r, r), r)
        # メイン
        pygame.draw.circle(surf, mid + (230,), (int(r*0.9), int(r*0.9)), int(r*0.85))
        # ハイライト
        pygame.draw.circle(surf, highlight + (160,), (int(r*0.6), int(r*0.6)), int(r*0.35))
        # 輪郭
        pygame.draw.circle(surf, (0,0,0,80), (r, r), r, 1)
        # ヒット時の白フラッシュをオーバーレイ
        if self.hit_flash_timer > 0.0:
            elapsed = self.hit_flash_duration - self.hit_flash_timer
            half = self.hit_flash_duration / 2.0
            if elapsed < half:
                # フェードイン
                alpha = int(255 * (elapsed / half))
            else:
                # フェードアウト
                alpha = int(255 * (1.0 - ((elapsed - half) / half)))
            alpha = max(0, min(255, alpha))
            # 白の円を重ねる
            flash_s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(flash_s, (255,255,255, alpha), (r, r), r)
            surf.blit(flash_s, (0,0), special_flags=0)

        screen.blit(surf, (int(sx - r), int(sy - r)))

    def on_hit(self):
        """敵が被弾したときに呼ぶ。白フラッシュをトリガーする."""
        # タイマをリセットして再生する
        self.hit_flash_timer = self.hit_flash_duration