import pygame
import random
import math
import os
import sys
from constants import *
from effects.items import GameItem, MoneyItem, ExperienceGem

def resource_path(relative_path):
    """PyInstallerで実行時にリソースファイルの正しいパスを取得する"""
    try:
        # PyInstallerで実行されている場合
        base_path = sys._MEIPASS
    except Exception:
        # 通常のPythonで実行されている場合
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class DustParticle:
    """砂埃パーティクルクラス"""
    def __init__(self, x, y):
        self.x = x + random.uniform(-20, 20)  # 少し散らす
        self.y = y + random.uniform(-5, 5)
        self.vx = random.uniform(-30, 30)  # 横方向の速度
        self.vy = random.uniform(-20, -5)  # 上方向の初期速度
        self.gravity = 80  # 重力
        self.size = random.uniform(2, 6)  # パーティクルサイズ
        self.life = random.uniform(0.8, 1.5)  # 生存時間（秒）
        self.max_life = self.life
        self.color = random.choice([
            (139, 121, 94),   # 茶色
            (160, 142, 115),  # 薄い茶色
            (101, 85, 67),    # 濃い茶色
            (184, 166, 139),  # ベージュ
        ])
    
    def update(self, dt=1/60):
        """パーティクルの更新"""
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt  # 重力を適用
        self.vx *= 0.98  # 空気抵抗
        self.life -= dt
        return self.life > 0
    
    def draw(self, screen, camera_x=0, camera_y=0):
        """パーティクルの描画"""
        if self.life <= 0:
            return
        
        # アルファ値を計算（時間とともにフェードアウト）
        alpha = int(255 * (self.life / self.max_life))
        alpha = max(0, min(255, alpha))
        
        # 描画位置
        draw_x = int(self.x - camera_x)
        draw_y = int(self.y - camera_y)
        
        # パーティクルサイズ
        current_size = max(1, int(self.size * (self.life / self.max_life)))
        
        # 砂埃らしい描画（小さな円）
        try:
            if alpha > 10:  # 透明すぎる場合は描画しない
                surf = pygame.Surface((current_size * 2 + 2, current_size * 2 + 2), pygame.SRCALPHA)
                color_with_alpha = (*self.color, alpha)
                pygame.draw.circle(surf, color_with_alpha, 
                                 (current_size + 1, current_size + 1), current_size)
                screen.blit(surf, (draw_x - current_size - 1, draw_y - current_size - 1))
        except Exception:
            pass

class ItemBox:
    """アイテムボックスクラス"""
    
    # 画像キャッシュ（クラス変数）
    _image_cache = {}
    
    @classmethod
    def _load_box_image(cls, box_type):
        """ボックス画像を読み込む（キャッシュ機能付き）"""
        if box_type in cls._image_cache:
            return cls._image_cache[box_type]
        
        # 画像ファイルパスを構築
        image_path = resource_path(os.path.join("assets", "icons", f"box{box_type}.png"))
        
        try:
            # ファイルの存在確認
            if not os.path.exists(image_path):
                print(f"[WARNING] Box image file not found: {image_path}")
                cls._image_cache[box_type] = None
                return None
                
            # 画像を読み込み
            image = pygame.image.load(image_path).convert_alpha()
            
            # BOX_SIZEにスケール
            image = pygame.transform.scale(image, (BOX_SIZE, BOX_SIZE))
            
            # キャッシュに保存
            cls._image_cache[box_type] = image
            return image
            
        except (pygame.error, FileNotFoundError) as e:
            print(f"[WARNING] Failed to load box image box{box_type}: {e}")
            cls._image_cache[box_type] = None
            return None
        except Exception as e:
            print(f"[ERROR] Unexpected error loading box image box{box_type}: {e}")
            cls._image_cache[box_type] = None
            return None

    def __init__(self, x, y, box_type=None):
        self.x = x
        self.y = y
        self.size = BOX_COLLISION_SIZE  # 当たり判定用サイズ
        self.display_size = BOX_SIZE    # 表示用サイズ
        
        # 初期位置が障害物と重なっている場合は調整
        self._adjust_spawn_position()
        
        # ボックスタイプを決定（指定されていない場合はランダム）
        if box_type is None:
            rand = random.random()
            if rand < BOX1_SPAWN_RATE:
                self.box_type = 1
            elif rand < BOX1_SPAWN_RATE + BOX2_SPAWN_RATE:
                self.box_type = 2
            else:
                self.box_type = 3
        else:
            # allow box_type 1-4; box4 reserved for boss drops
            self.box_type = max(1, min(4, int(box_type)))
        
        # ボックスタイプに応じてHPを設定
        if self.box_type == 1:
            self.hp = self.max_hp = BOX1_HP
        elif self.box_type == 2:
            self.hp = self.max_hp = BOX2_HP
        elif self.box_type == 4:
            self.hp = self.max_hp = BOX4_HP
        else:
            self.hp = self.max_hp = BOX3_HP
        
        # 状態管理
        self.destroyed = False
        self.is_dropping = False  # 落下中フラグを追加
        self.items_dropped = []  # 中から出たアイテムリスト
        
        # エフェクト用
        self.hit_flash_timer = 0.0
        self.hit_flash_duration = 0.3
        self.shake_timer = 0.0
        self.shake_duration = 0.2
        self.shake_intensity = 2
        
        # フロート効果用
        self.float_offset = 0.0
        self.float_speed = 2.0  # フロート速度
        self.float_amplitude = 3.0  # フロート振幅
        self.float_time = random.uniform(0, 2 * math.pi)  # フロート開始時間をランダムに
        
        # アニメーション用
        self.animation_time = random.uniform(0, 2 * math.pi)  # アニメーションタイムをランダム初期化
        
        # 落下アニメーション用
        self.spawn_time = pygame.time.get_ticks()
        self.drop_height = 80  # 落下開始高さ
        self.drop_duration = 300  # 落下時間（ミリ秒）
        self.bounce_height = 8   # バウンス高さ
        self.bounce_duration = 100  # バウンス時間（ミリ秒）
        self.is_dropping = True
        self.final_y = y  # 最終的なY座標
        
        # 落下アニメーション開始位置の設定
        self.y = y - self.drop_height  # ボックスを上空に配置
        
        # 砂埃エフェクト用
        self.dust_particles = []
        self.dust_spawned = False
        
        # 画像の読み込み
        self.image = self._load_box_image(self.box_type)
    
    def _adjust_spawn_position(self):
        """スポーン位置が障害物と重なっている場合、近くの通行可能な場所に移動"""
        if not USE_CSV_MAP:
            return
        
        try:
            from stage import get_stage_map
            stage_map = get_stage_map()
            
            # 現在位置をチェック
            if not self._is_position_blocked_internal(self.x, self.y, stage_map):
                return  # 問題なし
            
            # 周囲の通行可能な位置を探す
            search_radius = 80
            attempts = 30
            
            for _ in range(attempts):
                # ランダムな方向と距離で新しい位置を試す
                angle = random.uniform(0, 2 * math.pi)
                distance = random.uniform(self.size, search_radius)
                new_x = self.x + math.cos(angle) * distance
                new_y = self.y + math.sin(angle) * distance
                
                # ワールド境界内かチェック
                if (self.size <= new_x <= WORLD_WIDTH - self.size and 
                    self.size <= new_y <= WORLD_HEIGHT - self.size):
                    
                    # 障害物チェック
                    if not self._is_position_blocked_internal(new_x, new_y, stage_map):
                        self.x = new_x
                        self.y = new_y
                        return
            
            # 適切な位置が見つからない場合は、元の位置のままにする
            
        except Exception:
            # エラーが発生した場合は位置調整をスキップ
            pass
    
    def _is_position_blocked_internal(self, x, y, stage_map):
        """指定座標が障害物でブロックされているかチェック（内部用）"""
        # ボックスの四隅をチェック
        corners = [
            (x - self.size//2, y - self.size//2),
            (x + self.size//2, y - self.size//2),
            (x - self.size//2, y + self.size//2),
            (x + self.size//2, y + self.size//2),
        ]
        
        for corner_x, corner_y in corners:
            if stage_map.is_obstacle_at_world_pos(corner_x, corner_y):
                return True
        return False
        
        # 落下アニメーション用
        self.spawn_time = pygame.time.get_ticks()
        self.drop_height = 80  # 落下開始高さ
        self.drop_duration = 300  # 落下時間（ミリ秒）- 600から300に変更（2倍速）
        self.bounce_height = 8   # バウンス高さ
        self.bounce_duration = 100  # バウンス時間（ミリ秒）- 200から100に変更（2倍速）
        self.is_dropping = True
        self.final_y = y  # 最終的なY座標
        
        # 砂埃エフェクト用
        self.dust_particles = []
        self.dust_spawned = False
        
        # 画像読み込み
        self.image = self._load_box_image(self.box_type)
        
        # アニメーション用
        self.animation_time = 0.0
        self.float_offset = 0

    def take_damage(self, damage, player=None):
        """ダメージを受ける"""
        if self.destroyed:
            return False
        
        self.hp -= damage
        
        # ヒット時のエフェクト
        self.hit_flash_timer = self.hit_flash_duration
        self.shake_timer = self.shake_duration
        
        # HPが0以下になったら破壊
        if self.hp <= 0:
            self.destroy(player)
            return True  # 破壊された
        
        return False

    def destroy(self, player=None):
        """ボックスを破壊してアイテムを落とす"""
        if self.destroyed:
            return
        
        self.destroyed = True
        # Play box break sound (best-effort)
        try:
            from audio import audio
            audio.play_sound('box_break')
        except Exception:
            pass
        self.drop_items(player)

    def drop_items(self, player=None):
        """ボックスタイプに応じてアイテムを落とす"""
        items = []
        
        # アイテムドロップ位置を決定（落下中の場合は最終位置を使用）
        drop_x = self.x
        drop_y = self.final_y if hasattr(self, 'final_y') else self.y
        
        if self.box_type == 1:
            # Box1: コイン系のみ（money1～4の範囲で生成）
            items.append(MoneyItem(drop_x, drop_y, box_type=1))
            
        elif self.box_type == 2:
            # Box2: コイン90%, その他10%（マグネットサブアイテム所持時は調整）
            # マグネットサブアイテムのレベルを取得
            magnet_level = 0
            if player and hasattr(player, 'get_magnet_level'):
                try:
                    magnet_level = player.get_magnet_level()
                except Exception:
                    magnet_level = 0
            
            # マグネットレベルに応じてマグネット出現率を上げる
            # レベル1: +5%, レベル2: +10%, レベル3: +15%
            magnet_bonus = magnet_level * 0.05 if magnet_level > 0 else 0.0
            adjusted_magnet_rate = BOX2_MAGNET_RATE + magnet_bonus
            
            # 他のアイテム出現率を調整（マグネット増加分を他から削減）
            total_other_rate = BOX2_HEAL_RATE + BOX2_BOMB_RATE + BOX2_MAGNET_RATE
            adjusted_heal_rate = BOX2_HEAL_RATE * (1 - magnet_bonus / total_other_rate) if total_other_rate > 0 else BOX2_HEAL_RATE
            adjusted_bomb_rate = BOX2_BOMB_RATE * (1 - magnet_bonus / total_other_rate) if total_other_rate > 0 else BOX2_BOMB_RATE
            
            rand = random.random()
            if rand < BOX2_COIN_RATE:
                # コイン（money3～5の範囲で生成）
                items.append(MoneyItem(drop_x, drop_y, box_type=2))
            else:
                # その他のアイテム（調整済み出現率を使用）
                item_rand = random.random()
                remaining_rate = 1.0 - BOX2_COIN_RATE
                heal_threshold = adjusted_heal_rate / remaining_rate
                bomb_threshold = heal_threshold + (adjusted_bomb_rate / remaining_rate)
                
                if item_rand < heal_threshold:
                    items.append(GameItem(drop_x, drop_y, "heal"))
                elif item_rand < bomb_threshold:
                    items.append(GameItem(drop_x, drop_y, "bomb"))
                else:
                    items.append(GameItem(drop_x, drop_y, "magnet"))
                    
        elif self.box_type == 3:
            # Box3: お金・回復・ボム・マグネット各25%
            rand = random.random()
            if rand < BOX3_MONEY_RATE:
                # お金（money4～5の範囲で生成）
                items.append(MoneyItem(drop_x, drop_y, box_type=3))
            elif rand < BOX3_MONEY_RATE + BOX3_HEAL_RATE:
                items.append(GameItem(drop_x, drop_y, "heal"))
            elif rand < BOX3_MONEY_RATE + BOX3_HEAL_RATE + BOX3_BOMB_RATE:
                items.append(GameItem(drop_x, drop_y, "bomb"))
            else:
                items.append(GameItem(drop_x, drop_y, "magnet"))
        
        # アイテムをランダムな位置に散らす
        for i, item in enumerate(items):
            # ボックス周辺に散らす
            offset_angle = random.uniform(0, 2 * math.pi)
            offset_distance = random.uniform(20, 40)
            item.x += math.cos(offset_angle) * offset_distance
            item.y += math.sin(offset_angle) * offset_distance
        
        self.items_dropped = items

        # 特別処理: box_type 4 はボス専用の「レア箱」扱い
        if self.box_type == 4:
            # box4 は複数の高級報酬 (経験ジェム + 大量お金 + レアアイテム) を確実に落とす
            # 上書きして確実にレアな中身にする
            items = []
            # 経験値ジェムを複数
            for _ in range(3):
                items.append(ExperienceGem(drop_x, drop_y, value=50))
            # 高額のお金
            items.append(MoneyItem(drop_x, drop_y, amount=random.randint(MONEY4_AMOUNT_MIN, MONEY4_AMOUNT_MAX), box_type=4))
            # さらにレアアイテム（回復 or bomb or magnet のいずれか）を1つ
            rare = random.choice(["heal", "bomb", "magnet"])
            items.append(GameItem(drop_x, drop_y, rare))
            # 散らす位置
            for i, item in enumerate(items):
                offset_angle = random.uniform(0, 2 * math.pi)
                offset_distance = random.uniform(20, 50)
                item.x += math.cos(offset_angle) * offset_distance
                item.y += math.sin(offset_angle) * offset_distance
            self.items_dropped = items

    def update(self):
        """ボックスの更新処理"""
        if self.destroyed:
            return
        
        current_time = pygame.time.get_ticks()
        elapsed_time = current_time - self.spawn_time
        
        # 落下アニメーション処理
        if self.is_dropping:
            if elapsed_time < self.drop_duration:
                # 落下中：イージングを使った滑らかな落下
                progress = elapsed_time / self.drop_duration
                # イージングアウト（最初は速く、最後は遅く）
                eased_progress = 1 - (1 - progress) ** 3
                self.y = self.final_y - self.drop_height * (1 - eased_progress)
            elif elapsed_time < self.drop_duration + self.bounce_duration:
                # バウンス中
                bounce_progress = (elapsed_time - self.drop_duration) / self.bounce_duration
                # サイン波でバウンス効果
                bounce_offset = math.sin(bounce_progress * math.pi) * self.bounce_height
                self.y = self.final_y - bounce_offset
                
                # 着地時に砂埃エフェクトを生成（一度だけ）
                if not self.dust_spawned and bounce_progress > 0.8:
                    self._spawn_dust_particles()
                    self.dust_spawned = True
            else:
                # 落下アニメーション終了
                self.is_dropping = False
                self.y = self.final_y
                self.float_offset = 0.0  # フロートオフセットをリセット
        # 落下アニメーション終了後はフロートアニメーションを無効にする
        # else:
        #     # 通常のふわふわアニメーション（無効化）
        #     self.float_time += self.float_speed * (1.0 / 60.0)  # 60FPS想定
        #     self.float_offset = math.sin(self.float_time) * self.float_amplitude
        
        # 砂埃パーティクルの更新
        self.dust_particles = [p for p in self.dust_particles if p.update()]
        
        # エフェクトタイマー更新
        if self.hit_flash_timer > 0:
            self.hit_flash_timer -= 1.0 / 60.0  # 60FPS想定
            
        if self.shake_timer > 0:
            self.shake_timer -= 1.0 / 60.0
    
    def _spawn_dust_particles(self):
        """砂埃パーティクルを生成"""
        # 地面に着地した時の砂埃
        num_particles = random.randint(8, 15)
        for _ in range(num_particles):
            dust = DustParticle(self.x, self.final_y + self.display_size // 2)
            self.dust_particles.append(dust)

    def draw(self, screen, camera_x=0, camera_y=0):
        """ボックスの描画"""
        if self.destroyed:
            # 破壊されていても砂埃パーティクルは描画
            for dust in self.dust_particles:
                dust.draw(screen, camera_x, camera_y)
            return
        
        # 描画位置の計算（落下アニメーション中は現在のyを使用、通常時は静止）
        draw_x = self.x
        if self.is_dropping:
            draw_y = self.y  # 落下中は現在のy座標をそのまま使用
        else:
            draw_y = self.y  # 通常時も静止（フロート効果を無効化）
        
        # 揺れ効果
        if self.shake_timer > 0:
            shake_x = random.uniform(-self.shake_intensity, self.shake_intensity)
            shake_y = random.uniform(-self.shake_intensity, self.shake_intensity)
            draw_x += shake_x
            draw_y += shake_y
        
        # スクリーン座標に変換
        screen_x = int(draw_x - camera_x - self.display_size // 2)
        screen_y = int(draw_y - camera_y - self.display_size // 2)
        
        # 画像が読み込まれている場合
        if self.image:
            current_image = self.image
            
            # ヒット時のフラッシュ効果
            if self.hit_flash_timer > 0:
                # フラッシュ強度を計算
                flash_strength = self.hit_flash_timer / self.hit_flash_duration
                alpha = int(100 * flash_strength)
                
                # 白いオーバーレイを作成
                flash_surface = current_image.copy()
                white_overlay = pygame.Surface((BOX_SIZE, BOX_SIZE), pygame.SRCALPHA)
                white_overlay.fill((255, 255, 255, alpha))
                flash_surface.blit(white_overlay, (0, 0), special_flags=pygame.BLEND_ADD)
                current_image = flash_surface
            
            screen.blit(current_image, (screen_x, screen_y))
            
            # HPバーを描画（ダメージを受けている場合のみ、落下中は表示しない）
            if self.hp < self.max_hp and not self.is_dropping:
                self._draw_hp_bar(screen, screen_x, screen_y)
                
        else:
            # フォールバック: 色付きの正方形を描画
            self._draw_fallback_box(screen, screen_x, screen_y)
        
        # 砂埃パーティクルの描画
        for dust in self.dust_particles:
            dust.draw(screen, camera_x, camera_y)

    def _draw_hp_bar(self, screen, screen_x, screen_y):
        """HPバーの描画"""
        bar_width = self.display_size
        bar_height = 4
        bar_x = screen_x
        bar_y = screen_y - 8
        
        # 背景バー（赤）
        pygame.draw.rect(screen, (100, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        
        # HPバー（緑）
        hp_ratio = max(0, self.hp / self.max_hp)
        hp_width = int(bar_width * hp_ratio)
        if hp_width > 0:
            pygame.draw.rect(screen, (0, 200, 0), (bar_x, bar_y, hp_width, bar_height))
        
        # 枠線
        pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 1)

    def _draw_fallback_box(self, screen, screen_x, screen_y):
        """画像がない場合のフォールバック描画"""
        # ボックスタイプに応じた色
        if self.box_type == 1:
            base_color = (139, 69, 19)  # 茶色（木箱）
        elif self.box_type == 2:
            base_color = (169, 169, 169)  # 銀色（鉄箱）
        else:
            base_color = (255, 215, 0)  # 金色（宝箱）
        
        # メインの正方形
        rect = pygame.Rect(screen_x, screen_y, self.display_size, self.display_size)
        
        # ヒット時のフラッシュ効果
        if self.hit_flash_timer > 0:
            flash_strength = self.hit_flash_timer / self.hit_flash_duration
            flash_add = int(100 * flash_strength)
            draw_color = tuple(min(255, c + flash_add) for c in base_color)
        else:
            draw_color = base_color
        
        pygame.draw.rect(screen, draw_color, rect)
        
        # 枠線
        pygame.draw.rect(screen, (0, 0, 0), rect, 2)
        
        # タイプ番号を表示
        try:
            from resources import get_font
            font = get_font(16)
            if font:
                text = str(self.box_type)
                text_surf = font.render(text, True, (255, 255, 255))
                text_rect = text_surf.get_rect(center=rect.center)
                screen.blit(text_surf, text_rect)
        except Exception:
            pass
        
        # HPバーを描画（ダメージを受けている場合のみ）
        if self.hp < self.max_hp:
            self._draw_hp_bar(screen, screen_x, screen_y)

    def get_rect(self):
        """当たり判定用の矩形を取得"""
        # 落下中は当たり判定を無効にする
        if self.is_dropping:
            return pygame.Rect(0, 0, 0, 0)  # 空の矩形
        
        half_size = self.size // 2
        return pygame.Rect(
            int(self.x - half_size), 
            int(self.y - half_size), 
            self.size, 
            self.size
        )

    def is_destroyed(self):
        """破壊されているかを確認"""
        return self.destroyed

    def get_dropped_items(self):
        """落とされたアイテムのリストを取得"""
        return self.items_dropped
    
    def clear_dropped_items(self):
        """落とされたアイテムのリストをクリア"""
        self.items_dropped = []

    def is_far_from_player(self, player, margin=800):
        """プレイヤーから十分に離れているかどうかを判定"""
        dx = self.x - player.x
        dy = self.y - player.y
        distance_squared = dx * dx + dy * dy
        margin_squared = margin * margin
        return distance_squared > margin_squared


class BoxManager:
    """ボックスの出現と管理を行うクラス"""
    
    def __init__(self):
        self.boxes = []
        self.last_spawn_time = 0
        self.next_spawn_interval = self._get_random_spawn_interval()
    
    def _get_random_spawn_interval(self):
        """次のスポーン間隔をランダムに決定"""
        return random.randint(BOX_SPAWN_INTERVAL_MIN, BOX_SPAWN_INTERVAL_MAX)
    
    def update(self, current_time, player):
        """ボックスマネージャーの更新"""
        # 既存のボックスを更新
        for box in self.boxes:
            box.update()
        
        # プレイヤーから遠すぎるボックスを削除
        self.boxes = [box for box in self.boxes 
                     if not box.is_destroyed() and not box.is_far_from_player(player)]
        
        # 新しいボックスの出現判定
        if current_time - self.last_spawn_time >= self.next_spawn_interval:
            self._spawn_box_near_player(player)
            self.last_spawn_time = current_time
            self.next_spawn_interval = self._get_random_spawn_interval()
    
    def _spawn_box_near_player(self, player):
        """プレイヤーの近くにボックスを出現させる"""
        # プレイヤーから適度に離れた場所にスポーン
        min_distance = 200
        max_distance = 400
        
        for _ in range(20):  # 最大20回試行（増加）
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(min_distance, max_distance)
            
            spawn_x = player.x + math.cos(angle) * distance
            spawn_y = player.y + math.sin(angle) * distance
            
            # ワールド境界内にクランプ
            spawn_x = max(50, min(WORLD_WIDTH - 50, spawn_x))
            spawn_y = max(50, min(WORLD_HEIGHT - 50, spawn_y))
            
            # 障害物との衝突チェック
            if self._is_position_blocked(spawn_x, spawn_y):
                continue
            
            # 他のボックスから十分離れているかチェック
            too_close = False
            for existing_box in self.boxes:
                if not existing_box.is_destroyed():
                    dx = spawn_x - existing_box.x
                    dy = spawn_y - existing_box.y
                    if dx * dx + dy * dy < 100 * 100:  # 100ピクセル未満は近すぎる
                        too_close = True
                        break
            
            if not too_close:
                # ボックス生成
                new_box = ItemBox(spawn_x, spawn_y)
                self.boxes.append(new_box)
                # print(f"[DEBUG] Spawned box{new_box.box_type} at ({spawn_x:.1f}, {spawn_y:.1f})")
                break
    
    def _is_position_blocked(self, x, y):
        """指定座標が障害物でブロックされているかチェック"""
        # マップが有効でない場合は障害物なし
        if not USE_CSV_MAP:
            return False
        
        try:
            from stage import get_stage_map
            stage_map = get_stage_map()
            
            # ボックスサイズの半分だけ余裕を持たせてチェック
            box_size = BOX_COLLISION_SIZE
            corners = [
                (x - box_size//2, y - box_size//2),
                (x + box_size//2, y - box_size//2),
                (x - box_size//2, y + box_size//2),
                (x + box_size//2, y + box_size//2),
            ]
            
            for corner_x, corner_y in corners:
                if stage_map.is_obstacle_at_world_pos(corner_x, corner_y):
                    return True
            return False
            
        except Exception:
            # エラーが発生した場合は障害物なしと判定
            return False
    
    def get_all_boxes(self):
        """すべてのボックスを取得（落下中でないもののみ）"""
        return [box for box in self.boxes if not box.is_destroyed() and not box.is_dropping]
    
    def get_all_dropped_items(self):
        """すべてのボックスから落とされたアイテムを取得"""
        all_items = []
        for box in self.boxes:
            if box.is_destroyed():
                all_items.extend(box.get_dropped_items())
                box.clear_dropped_items()  # アイテムを渡したらクリア
        return all_items
    
    def draw_all(self, screen, camera_x=0, camera_y=0):
        """すべてのボックスを描画（砂埃パーティクルも含む）"""
        for box in self.boxes:
            box.draw(screen, camera_x, camera_y)  # 破壊されたボックスでも砂埃を描画
    
    def clear_destroyed_boxes(self):
        """破壊されたボックスをリストから削除（砂埃パーティクルが残っている場合は保持）"""
        self.boxes = [box for box in self.boxes 
                     if not box.is_destroyed() or len(box.dust_particles) > 0]
