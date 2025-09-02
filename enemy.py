import pygame
import random
import math
import os
from constants import *

class Enemy:
    # 画像キャッシュ（クラス変数）
    _image_cache = {}
    
    @classmethod
    def _load_enemy_image(cls, enemy_type, enemy_level):
        """敵の画像を読み込む（キャッシュ機能付き）"""
        # キャッシュキーを作成
        cache_key = f"{enemy_type:02d}-{enemy_level:02d}"
        
        # キャッシュから画像を取得
        if cache_key in cls._image_cache:
            return cls._image_cache[cache_key]
        
        # 画像ファイルパスを構築
        image_path = os.path.join("assets", "character", "enemy", f"{cache_key}.png")
        
        try:
            # 画像を読み込み
            image = pygame.image.load(image_path).convert_alpha()
            
            # レベルに応じたサイズを計算（レベル1: 32px, レベル5: 48px）
            base_size = 32
            max_size = 48
            size = base_size + int((max_size - base_size) * (enemy_level - 1) / 4)
            
            # レベルに応じたサイズにスケール
            image = pygame.transform.scale(image, (size, size))
            
            # HSVを調整
            image = cls._adjust_hsv(image, ENEMY_IMAGE_HUE_SHIFT, ENEMY_IMAGE_SATURATION, ENEMY_IMAGE_VALUE)
            
            # 左右反転用の画像も作成
            flipped_image = pygame.transform.flip(image, True, False)
            
            # キャッシュに保存（通常版と反転版、サイズ情報も含む）
            cls._image_cache[cache_key] = {
                'left': image,      # 左向き（元画像）
                'right': flipped_image,  # 右向き（反転）
                'size': size        # 実際のサイズ
            }
            
            return cls._image_cache[cache_key]
            
        except (pygame.error, FileNotFoundError):
            # 画像が見つからない場合はNoneを返す
            cls._image_cache[cache_key] = None
            return None
    
    @classmethod
    def _adjust_hsv(cls, surface, hue_shift=0.0, saturation_factor=1.0, value_factor=1.0):
        """画像のHSV値を調整する
        Args:
            surface: 調整対象のサーフェス
            hue_shift: 色相シフト（-1.0～1.0）
            saturation_factor: 彩度倍率（0.0～2.0）
            value_factor: 明度倍率（0.0～2.0）
        """
        if hue_shift == 0.0 and saturation_factor == 1.0 and value_factor == 1.0:
            return surface  # 調整不要
        
        # 新しいサーフェスを作成
        adjusted_surface = surface.copy()
        
        # ピクセル配列にアクセス
        width, height = surface.get_size()
        
        # ピクセルごとにHSVを調整
        for x in range(width):
            for y in range(height):
                color = surface.get_at((x, y))
                r, g, b, a = color
                
                # アルファが0の場合（透明）は処理をスキップ
                if a == 0:
                    continue
                
                # RGBをHSVに変換
                import colorsys
                h, s, v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
                
                # HSV値を調整
                # 色相シフト（0-1の範囲で循環）
                h = (h + hue_shift) % 1.0
                
                # 彩度調整
                s = s * saturation_factor
                s = max(0.0, min(1.0, s))  # 0-1の範囲にクランプ
                
                # 明度調整
                v = v * value_factor
                v = max(0.0, min(1.0, v))  # 0-1の範囲にクランプ
                
                # HSVをRGBに戻す
                r_new, g_new, b_new = colorsys.hsv_to_rgb(h, s, v)
                
                # 0-255の範囲に変換
                r_new = int(r_new * 255)
                g_new = int(g_new * 255)
                b_new = int(b_new * 255)
                
                # 新しい色を設定
                adjusted_surface.set_at((x, y), (r_new, g_new, b_new, a))
        
        return adjusted_surface
    
    def __init__(self, screen, game_time, spawn_x=None, spawn_y=None, spawn_side=None):
        self.screen = screen
        
        # ヒット時のフラッシュ用タイマ（秒）
        self.hit_flash_timer = 0.0
        self.hit_flash_duration = 0.25  # フェードイン+フェードアウトの合計時間
        
        # 全体的にやや遅めに調整
        # base_speed を導入して、プレイヤーの speed 変更の影響を受けないようにする
        self.base_speed = 1.5
        self.speed = self.base_speed
        
        # 敵の種類をランダムに決定（game_timeに応じて変化）
        self.enemy_type = self.get_random_enemy_type(game_time)
        
        # レベルに応じたサイズを設定（レベル1: 15px, レベル5: 24px の半径）
        # 画像サイズが32-48pxなので、当たり判定は少し小さめに設定
        base_radius = 15
        max_radius = 24
        self.size = base_radius + int((max_radius - base_radius) * (self.enemy_type - 1) / 4)
        
        # 行動パターンをランダムに決定
        self.behavior_type = self.get_random_behavior_type(game_time)
        
        # 行動パターン用の変数
        self.initial_direction = None  # 直進タイプ用の初期方向
        self.target_distance = 200  # 距離保持タイプ用の目標距離（倍に拡大）
        self.attack_cooldown = 0  # 攻撃クールダウン（ミリ秒）
        self.last_attack_time = 0  # 最後の攻撃時刻
        self.projectiles = []  # 敵が発射した弾丸
        
        # 生存時間管理
        self.spawn_time = pygame.time.get_ticks()  # 生成時刻
        
        # 歩行アニメーション用変数
        self.animation_time = 0.0  # アニメーション用タイマー
        self.is_moving = False     # 移動しているかどうか
        self.last_x = self.x if hasattr(self, 'x') else 0
        self.last_y = self.y if hasattr(self, 'y') else 0
        
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

    def get_random_behavior_type(self, game_time):
        """行動パターンをランダムに決定
        1: プレイヤーに寄ってくる（追跡）
        2: プレイヤーに向かうがそのまま直進して画面端に消える
        3: プレイヤーから一定の距離を保ち、魔法の杖のような弾を発射する
        4: 遅い速度でプレイヤーに近づき、遠距離攻撃も行う
        """
        if game_time <= 30:  # 序盤は単純な行動のみ
            rand = random.random()
            if rand < 0.8:    # 80%
                return 1      # 追跡
            else:            # 20%
                return 2      # 直進
        elif game_time <= 70:  # 中盤から射撃敵も登場
            rand = random.random()
            if rand < 0.5:    # 50%
                return 1      # 追跡
            elif rand < 0.7:  # 20%
                return 2      # 直進
            elif rand < 0.85: # 15%
                return 3      # 距離保持射撃
            else:            # 15%
                return 4      # 固定砲台
        else:                # 終盤は多様な行動
            rand = random.random()
            if rand < 0.4:    # 40%
                return 1      # 追跡
            elif rand < 0.55: # 15%
                return 2      # 直進
            elif rand < 0.75: # 20%
                return 3      # 距離保持射撃
            else:            # 25%
                return 4      # 固定砲台

    def setup_enemy_stats(self):
        # 基本ステータス（タイプに応じて設定）
        base_stats = {
            1: {'hp': 10, 'speed': 1.125, 'damage': 2},
            2: {'hp': 20, 'speed': 1.5, 'damage': 4},
            3: {'hp': 30, 'speed': 1.875, 'damage': 6},
            4: {'hp': 40, 'speed': 2.0, 'damage': 8},
            5: {'hp': 50, 'speed': 2.25, 'damage': 10}
        }
        
        stats = base_stats.get(self.enemy_type, base_stats[1])
        self.hp = stats['hp']
        self.base_speed = stats['speed']
        self.damage = stats['damage']
        
        # 行動パターンに応じた色設定（レベルに応じて彩度を変える）
        # 彩度設定：レベル1は低彩度（白っぽい）、レベル5は高彩度（鮮やか）
        saturation = 0.2 + (self.enemy_type - 1) * 0.2  # 0.2-1.0の範囲
        base_value = 200  # 明度は固定
        
        if self.behavior_type == 1:  # 追跡 - 赤
            # 赤色: 彩度が低いと白っぽい、高いと鮮やかな赤
            self.color = self._hsv_to_rgb(0.0, saturation, base_value)
        elif self.behavior_type == 2:  # 直進 - 青
            # 青色: 色相240度
            self.color = self._hsv_to_rgb(240.0, saturation, base_value)
        elif self.behavior_type == 3:  # 距離保持射撃 - 緑
            # 緑色: 色相120度
            self.color = self._hsv_to_rgb(120.0, saturation, base_value)
        elif self.behavior_type == 4:  # 固定砲台 - 橙
            # オレンジ色: 色相30度
            self.color = self._hsv_to_rgb(30.0, saturation, base_value)
        
        # 行動パターンに応じた調整
        if self.behavior_type == 2:  # 直進タイプ
            self.base_speed *= 2.0  # 速度アップ
        elif self.behavior_type == 3:  # 距離保持射撃
            self.base_speed *= 0.35  # 速度ダウン（半分に減速）
            self.attack_cooldown = 8000  # 8秒間隔で攻撃（2秒から4倍に延長）
        elif self.behavior_type == 4:  # 遅速追跡（旧固定砲台）
            self.base_speed *= 0.25  # 通常の5分の1の速度で移動
            self.attack_cooldown = 6000  # 6秒間隔で攻撃
            # HP調整なし（デフォルト値のまま）
        
        self.speed = self.base_speed
        
        # 画像の読み込み
        self.images = self._load_enemy_image(self.behavior_type, self.enemy_type)
        self.facing_right = True  # 向いている方向（True: 右, False: 左）
        self.last_movement_x = 0  # 最後の移動方向を記録

    def move(self, player):
        """行動パターンに応じた移動処理"""
        new_x, new_y = self.x, self.y
        
        if self.behavior_type == 1:
            # 1. プレイヤーに寄ってくる（追跡）
            angle = math.atan2(player.y - self.y, player.x - self.x)
            new_x = self.x + math.cos(angle) * self.base_speed
            new_y = self.y + math.sin(angle) * self.base_speed
            
        elif self.behavior_type == 2:
            # 2. プレイヤーに向かうがそのまま直進して画面端に消える
            if self.initial_direction is None:
                # 初回のみプレイヤー方向を計算して保存
                self.initial_direction = math.atan2(player.y - self.y, player.x - self.x)
            
            # 初期方向に直進
            new_x = self.x + math.cos(self.initial_direction) * self.base_speed
            new_y = self.y + math.sin(self.initial_direction) * self.base_speed
            
        elif self.behavior_type == 3:
            # 3. プレイヤーから一定の距離を保ち、魔法の杖のような弾を発射する
            distance_to_player = math.hypot(player.x - self.x, player.y - self.y)
            
            if distance_to_player < self.target_distance - 20:
                # プレイヤーに近すぎる場合は離れる（許容範囲も倍に）
                angle = math.atan2(self.y - player.y, self.x - player.x)  # プレイヤーから離れる方向
                new_x = self.x + math.cos(angle) * self.base_speed
                new_y = self.y + math.sin(angle) * self.base_speed
            elif distance_to_player > self.target_distance + 20:
                # プレイヤーから遠すぎる場合は近づく（許容範囲も倍に）
                angle = math.atan2(player.y - self.y, player.x - self.x)  # プレイヤーに向かう方向
                new_x = self.x + math.cos(angle) * self.base_speed
                new_y = self.y + math.sin(angle) * self.base_speed
            # 適切な距離の場合は移動しない
            
        elif self.behavior_type == 4:
            # 4. 遅い速度でプレイヤーに近づく
            angle = math.atan2(player.y - self.y, player.x - self.x)
            new_x = self.x + math.cos(angle) * self.base_speed
            new_y = self.y + math.sin(angle) * self.base_speed
        
        # 障害物との衝突判定（マップが有効な場合のみ）
        if USE_STAGE_MAP and (new_x != self.x or new_y != self.y):
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
        
        # 移動方向に基づいて向きを更新
        movement_x = new_x - getattr(self, '_prev_x', self.x)
        if abs(movement_x) > 0.1:  # 小さな移動は無視
            self.facing_right = movement_x > 0
        
        # 前回の位置を記録
        self._prev_x = self.x
        self._prev_y = self.y
        
        # 歩行アニメーション更新
        # 移動しているかどうかを判定
        movement_distance = math.hypot(self.x - self.last_x, self.y - self.last_y)
        self.is_moving = movement_distance > 0.1  # 微小な移動は無視
        
        # アニメーション時間の更新
        if self.is_moving:
            self.animation_time += 1.0 / 60.0  # 60FPS想定でタイマー更新
        
        # 現在位置を記録（次フレームの比較用）
        self.last_x = self.x
        self.last_y = self.y

        # ヒットフラッシュのタイマを減算（フレーム毎に呼ばれることを想定、60FPS基準）
        if self.hit_flash_timer > 0.0:
            self.hit_flash_timer = max(0.0, self.hit_flash_timer - (1.0/60.0))

    def draw(self, screen, camera_x=0, camera_y=0):
        # ワールド座標からスクリーン座標に変換
        sx = int(self.x - camera_x)
        sy = int(self.y - camera_y)

        # 画像がある場合は画像を描画、ない場合は従来の円を描画
        if self.images and isinstance(self.images, dict) and 'right' in self.images and 'left' in self.images:
            # 向きに応じて画像を選択
            image = self.images['right'] if self.facing_right else self.images['left']
            
            # 画像が正常に取得できた場合のみ描画
            if image is not None:
                # 画像のサイズを取得（レベルに応じて変化）
                image_size = self.images.get('size', 32)
                
                # 歩行アニメーション効果を計算
                foot_offset_y = 0
                
                if (self.is_moving and ENABLE_ENEMY_WALK_ANIMATION and 
                    ENEMY_WALK_BOB_AMPLITUDE > 0):  # アニメーションが有効な場合のみ
                    # 足部分の上下振動（1ピクセル上下）
                    foot_raw = math.sin(self.animation_time * ENEMY_WALK_BOB_SPEED)
                    foot_offset_y = 1 if foot_raw > 0 else -1
                
                # 画像の基本位置を計算（スウェイなし、固定位置）
                base_x = sx - image_size // 2
                base_y = sy - image_size // 2
                
                # 使用する画像を決定
                current_image = image
                
                # アニメーションが無効または足が動かない場合は通常描画
                if (not ENABLE_ENEMY_WALK_ANIMATION or not self.is_moving or 
                    ENEMY_WALK_BOB_AMPLITUDE <= 0 or foot_offset_y == 0):
                    # 通常の1回描画（最適化）
                    if self.hit_flash_timer > 0.0:
                        # フラッシュ効果
                        elapsed = self.hit_flash_duration - self.hit_flash_timer
                        half = self.hit_flash_duration / 2.0
                        if elapsed < half:
                            alpha = int(255 * (elapsed / half))
                        else:
                            alpha = int(255 * ((self.hit_flash_duration - elapsed) / half))
                        
                        flashed_image = current_image.copy()
                        white_surface = pygame.Surface((image_size, image_size), pygame.SRCALPHA)
                        white_surface.fill((255, 255, 255, alpha))
                        flashed_image.blit(white_surface, (0, 0), special_flags=pygame.BLEND_ADD)
                        screen.blit(flashed_image, (base_x, base_y))
                    else:
                        # 通常描画
                        screen.blit(current_image, (base_x, base_y))
                    return  # 早期リターンで以下の処理をスキップ
                
                # 以下はアニメーション有効時のみ実行
                # 元画像のサイズ（32, 36, 40, 44, 48のいずれか）
                original_size = 32  # 基準サイズ
                scale_factor = image_size / original_size
                
                # 足部分の領域を計算（向きに応じて左右反転）
                if self.facing_right:
                    # 右向き時：左下部分を動かす（反転画像では右足に見える）
                    foot_start_x = int(0 * scale_factor)   # 画像の左端から
                    foot_end_x = int(16 * scale_factor)    # 画像の左半分まで
                else:
                    # 左向き時：右下部分を動かす（反転画像では左足に見える）
                    foot_start_x = int(16 * scale_factor)  # 画像の右半分から
                    foot_end_x = int(32 * scale_factor)    # 画像の右端まで
                
                foot_start_y = int(16 * scale_factor)  # 画像の下半分から  
                foot_end_y = int(32 * scale_factor)    # 画像の下端まで
                foot_width = foot_end_x - foot_start_x
                foot_height = foot_end_y - foot_start_y
                
                # 足部分以外の領域（メイン画像）
                main_surface = current_image.copy()
                
                # 足部分を抜き出し
                foot_rect = pygame.Rect(foot_start_x, foot_start_y, foot_width, foot_height)
                foot_surface = current_image.subsurface(foot_rect)
                
                # 足部分をメイン画像から透明にする（足が二重に描画されないように）
                transparent_rect = pygame.Surface((foot_width, foot_height), pygame.SRCALPHA)
                transparent_rect.fill((0, 0, 0, 0))  # 完全透明
                main_surface.blit(transparent_rect, (foot_start_x, foot_start_y))
                
                # 描画位置を計算
                main_x = base_x
                main_y = base_y
                foot_x = base_x + foot_start_x
                foot_y = base_y + foot_start_y + int(foot_offset_y)
                
                # ヒット時のフラッシュ効果
                if self.hit_flash_timer > 0.0:
                    elapsed = self.hit_flash_duration - self.hit_flash_timer
                    half = self.hit_flash_duration / 2.0
                    if elapsed < half:
                        # フェードイン
                        alpha = int(255 * (elapsed / half))
                    else:
                        # フェードアウト
                        alpha = int(255 * ((self.hit_flash_duration - elapsed) / half))
                    
                    # メイン画像のフラッシュ効果
                    flashed_main = main_surface.copy()
                    white_surface_main = pygame.Surface((image_size, image_size), pygame.SRCALPHA)
                    white_surface_main.fill((255, 255, 255, alpha))
                    flashed_main.blit(white_surface_main, (0, 0), special_flags=pygame.BLEND_ADD)
                    screen.blit(flashed_main, (main_x, main_y))
                    
                    # 足部分のフラッシュ効果
                    flashed_foot = foot_surface.copy()
                    white_surface_foot = pygame.Surface((foot_width, foot_height), pygame.SRCALPHA)
                    white_surface_foot.fill((255, 255, 255, alpha))
                    flashed_foot.blit(white_surface_foot, (0, 0), special_flags=pygame.BLEND_ADD)
                    screen.blit(flashed_foot, (foot_x, foot_y))
                else:
                    # 通常描画（メイン画像 + 足部分）
                    screen.blit(main_surface, (main_x, main_y))
                    screen.blit(foot_surface, (foot_x, foot_y))
        else:
            # 画像がない場合は従来の円描画
            self._draw_circle(screen, sx, sy)
    
    def _draw_circle(self, screen, sx, sy):
        """従来の円描画（画像がない場合のフォールバック）"""
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
        
        # 行動パターン識別用の小さなアイコンを描画
        self._draw_behavior_icon(screen, sx, sy)
    
    def _draw_behavior_icon(self, screen, sx, sy):
        """行動パターン識別用のアイコンを描画"""
        icon_size = 4
        icon_y_offset = -self.size - 8
        
        if self.behavior_type == 1:  # 追跡 - 矢印
            # 小さな矢印を描画
            points = [
                (sx, sy + icon_y_offset - icon_size),
                (sx - icon_size//2, sy + icon_y_offset + icon_size//2),
                (sx + icon_size//2, sy + icon_y_offset + icon_size//2)
            ]
            pygame.draw.polygon(screen, (255, 255, 255), points)
        elif self.behavior_type == 2:  # 直進 - 直線
            pygame.draw.line(screen, (255, 255, 255), 
                           (sx - icon_size, sy + icon_y_offset), 
                           (sx + icon_size, sy + icon_y_offset), 2)
        elif self.behavior_type == 3:  # 距離保持射撃 - 円
            pygame.draw.circle(screen, (255, 255, 255), 
                             (sx, sy + icon_y_offset), icon_size, 1)
        elif self.behavior_type == 4:  # 遅速追跡 - 太矢印
            # 遅い移動を表す太めの矢印を描画
            points = [
                (sx, sy + icon_y_offset - icon_size),
                (sx - icon_size//2, sy + icon_y_offset),
                (sx - icon_size//4, sy + icon_y_offset),
                (sx - icon_size//4, sy + icon_y_offset + icon_size//2),
                (sx + icon_size//4, sy + icon_y_offset + icon_size//2),
                (sx + icon_size//4, sy + icon_y_offset),
                (sx + icon_size//2, sy + icon_y_offset)
            ]
            pygame.draw.polygon(screen, (255, 255, 255), points)

    def on_hit(self):
        """敵が被弾したときに呼ぶ。白フラッシュをトリガーする."""
        # タイマをリセットして再生する
        self.hit_flash_timer = self.hit_flash_duration

    def update_attack(self, player):
        """攻撃処理（射撃タイプの敵のみ）"""
        if self.behavior_type not in [3, 4]:
            return  # 射撃タイプ以外は攻撃しない
        
        current_time = pygame.time.get_ticks()
        if current_time - self.last_attack_time >= self.attack_cooldown:
            # プレイヤーに向けて弾丸を発射
            angle = math.atan2(player.y - self.y, player.x - self.x)
            projectile = EnemyProjectile(self.x, self.y, angle, self.damage // 2, self.behavior_type, self.enemy_type)
            self.projectiles.append(projectile)
            self.last_attack_time = current_time

    def update_projectiles(self, player=None):
        """弾丸の更新処理"""
        # 有効期限切れや画面外の弾丸を削除
        valid_projectiles = []
        for p in self.projectiles:
            if p.is_expired() or not p.is_on_screen():
                continue
            
            # プレイヤーから非常に遠い弾丸も削除（パフォーマンス向上）
            if player is not None:
                dx = p.x - player.x
                dy = p.y - player.y
                if dx * dx + dy * dy > 1000000:  # 1000ピクセル以上離れたら削除
                    continue
            
            valid_projectiles.append(p)
        
        self.projectiles = valid_projectiles
        
        # 弾丸の移動
        for projectile in self.projectiles:
            projectile.update()

    def draw_projectiles(self, screen, camera_x=0, camera_y=0):
        """弾丸の描画"""
        for projectile in self.projectiles:
            projectile.draw(screen, camera_x, camera_y)

    def get_projectiles(self):
        """弾丸のリストを取得（プレイヤーとの衝突判定用）"""
        return self.projectiles

    def is_off_screen(self):
        """敵が画面外に出たかどうかを判定（直進タイプ用）"""
        margin = 100
        return (self.x < -margin or self.x > WORLD_WIDTH + margin or 
                self.y < -margin or self.y > WORLD_HEIGHT + margin)

    def is_far_from_player(self, player, margin=800):
        """プレイヤーから十分に離れているかどうかを判定（視界外削除用）"""
        dx = self.x - player.x
        dy = self.y - player.y
        distance_squared = dx * dx + dy * dy
        margin_squared = margin * margin
        return distance_squared > margin_squared

    def is_in_screen_bounds(self, player, screen_width=1280, screen_height=720, margin=300):
        """プレイヤーを中心とした画面範囲内にいるかを判定（マージン付き）
        
        Args:
            player: プレイヤーオブジェクト
            screen_width: 画面幅
            screen_height: 画面高さ  
            margin: 画面端からの余裕（この範囲内では削除しない）
        """
        # プレイヤーを中心とした画面範囲を計算（適切なマージンで保護）
        half_width = screen_width / 2 + margin
        half_height = screen_height / 2 + margin
        
        # 敵の位置が画面範囲内かチェック
        dx = abs(self.x - player.x)
        dy = abs(self.y - player.y)
        
        # 画面境界チェック
        is_in_bounds = dx <= half_width and dy <= half_height
        
        return is_in_bounds

    def should_be_removed_by_time(self):
        """生存時間に基づく削除判定（距離保持射撃用のみ）"""
        if self.behavior_type == 3:  # 距離保持射撃
            # 距離保持射撃は45秒で削除
            return pygame.time.get_ticks() - self.spawn_time > 45000
        else:
            # その他のタイプは時間制限なし
            return False

    def get_type_info(self):
        """敵の種類情報を取得（デバッグ用）"""
        behavior_names = {
            1: "追跡",
            2: "直進", 
            3: "距離保持",
            4: "遅速追跡"
        }
        
        color_names = {
            1: "赤",
            2: "青", 
            3: "緑",
            4: "橙"
        }
        
        return {
            'behavior': behavior_names.get(self.behavior_type, "不明"),
            'color': color_names.get(self.behavior_type, "不明"),
            'level': self.enemy_type,
            'hp': self.hp,
            'damage': self.damage,
            'speed': self.base_speed
        }

    def _hsv_to_rgb(self, hue, saturation, value):
        """HSV色空間からRGB色空間に変換
        Args:
            hue: 色相（0-360度）
            saturation: 彩度（0.0-1.0）
            value: 明度（0-255）
        Returns:
            (r, g, b) タプル（0-255の値）
        """
        import colorsys
        
        # HSVをRGBに変換（colorsysは0-1の範囲で動作）
        h = hue / 360.0
        s = saturation
        v = value / 255.0
        
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        
        # 0-255の範囲に変換して整数化
        return (
            max(0, min(255, int(r * 255))),
            max(0, min(255, int(g * 255))),
            max(0, min(255, int(b * 255)))
        )


class EnemyProjectile:
    """敵が発射する弾丸クラス"""
    def __init__(self, x, y, angle, damage, behavior_type=3, enemy_level=1):
        self.x = x
        self.y = y
        self.angle = angle
        self.damage = damage
        self.behavior_type = behavior_type
        self.enemy_level = enemy_level  # 敵のレベルを記録
        self.speed = 2.0  # 弾丸の速度（半分に減速）
        self.size = 18  # 弾丸のサイズ（1.5倍に拡大：12 * 1.5 = 18）
        self.lifetime = 3000  # 3秒で消滅（ミリ秒）
        self.created_time = pygame.time.get_ticks()
        
        # 速度ベクトルを計算
        self.vx = math.cos(angle) * self.speed
        self.vy = math.sin(angle) * self.speed
        
        # 敵と同じ彩度設定で弾丸の色を決定
        self._setup_bullet_color()

    def _setup_bullet_color(self):
        """敵のレベルと行動パターンに応じた弾丸の色を設定"""
        # 彩度設定：レベル1は低彩度（白っぽい）、レベル5は高彩度（鮮やか）
        saturation = 0.2 + (self.enemy_level - 1) * 0.2  # 0.2-1.0の範囲
        base_value = 200  # 明度は固定
        
        if self.behavior_type == 1:  # 追跡 - 赤
            self.base_color = self._hsv_to_rgb(0.0, saturation, base_value)
        elif self.behavior_type == 2:  # 直進 - 青
            self.base_color = self._hsv_to_rgb(240.0, saturation, base_value)
        elif self.behavior_type == 3:  # 距離保持射撃 - 緑
            self.base_color = self._hsv_to_rgb(120.0, saturation, base_value)
        elif self.behavior_type == 4:  # 固定砲台 - 橙
            self.base_color = self._hsv_to_rgb(30.0, saturation, base_value)
        else:  # デフォルト（青）
            self.base_color = self._hsv_to_rgb(240.0, saturation, base_value)

    def _hsv_to_rgb(self, hue, saturation, value):
        """HSV色空間からRGB色空間に変換"""
        import colorsys
        
        # HSVをRGBに変換（colorsysは0-1の範囲で動作）
        h = hue / 360.0
        s = saturation
        v = value / 255.0
        
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        
        # 0-255の範囲に変換して整数化
        return (
            max(0, min(255, int(r * 255))),
            max(0, min(255, int(g * 255))),
            max(0, min(255, int(b * 255)))
        )

    def update(self):
        """弾丸の移動処理"""
        self.x += self.vx
        self.y += self.vy

    def draw(self, screen, camera_x=0, camera_y=0):
        """弾丸の描画（彩度ベースの色設定）"""
        sx = int(self.x - camera_x)
        sy = int(self.y - camera_y)
        
        r = self.size
        surf = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        
        # 基本色から明度の異なるバリエーションを作成
        r_base, g_base, b_base = self.base_color
        
        # 外側の光輪（基本色、透明度低め）
        outer_color = (r_base//2, g_base//2, b_base//2, 60)
        pygame.draw.circle(surf, outer_color, (r, r), r)
        
        # 内側のコア（基本色、透明度中）
        core_color = (r_base, g_base, b_base, 180)
        pygame.draw.circle(surf, core_color, (r, r), r//2)
        
        # 中心点（基本色を明るく、透明度高め）
        center_r = min(255, int(r_base * 1.2))
        center_g = min(255, int(g_base * 1.2))
        center_b = min(255, int(b_base * 1.2))
        center_color = (center_r, center_g, center_b, 220)
        pygame.draw.circle(surf, center_color, (r, r), r//3)
        
        screen.blit(surf, (sx - r, sy - r))

    def is_expired(self):
        """弾丸が有効期限切れかどうかを判定"""
        return pygame.time.get_ticks() - self.created_time >= self.lifetime

    def is_on_screen(self):
        """弾丸が画面内（ワールド内）にあるかどうかを判定"""
        margin = 50
        return (-margin <= self.x <= WORLD_WIDTH + margin and 
                -margin <= self.y <= WORLD_HEIGHT + margin)

    def get_rect(self):
        """衝突判定用の矩形を取得"""
        return pygame.Rect(self.x - self.size//2, self.y - self.size//2, self.size, self.size)