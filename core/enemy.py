import pygame
import random
import math
import os
import sys
import colorsys
import csv
import time
from constants import *

def resource_path(relative_path):
    """PyInstallerで実行時にリソースファイルの正しいパスを取得する"""
    try:
        # PyInstallerで実行されている場合
        base_path = sys._MEIPASS
    except Exception:
        # 通常のPythonで実行されている場合
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class Enemy:
    # 画像キャッシュ（クラス変数）
    _image_cache = {}
    
    # エネミーステータスのキャッシュ
    _enemy_stats = {}
    _stats_loaded = False
    
    # ボス設定のキャッシュ
    _boss_stats = {}
    _boss_stats_loaded = False
    
    @classmethod
    def load_enemy_stats(cls):
        """エネミーステータスをCSVファイルから読み込む"""
        if cls._stats_loaded:
            return
            
        csv_path = resource_path("data/enemy_stats.csv")
        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    enemy_no = int(row['enemy_no'])  # enemy_noをキーとして使用
                    cls._enemy_stats[enemy_no] = {
                        'type': int(row['type']),  # 行動パターン用に保持
                        'level': int(row['level']),  # レベル情報も保持
                        'base_hp': int(row['base_hp']),
                        'base_speed': float(row['base_speed']),
                        'base_damage': int(row['base_damage']),
                        'speed_multiplier': float(row['speed_multiplier']),
                        'attack_cooldown': int(row['attack_cooldown']),
                        'image_file': row['image_file'],
                        'image_size': int(row['image_size']),
                        'projectile_speed': float(row['projectile_speed']) if row['projectile_speed'] else 3.0,
                        'description': row['description']
                    }
            cls._stats_loaded = True
            print(f"[INFO] Loaded {len(cls._enemy_stats)} enemy configurations from {csv_path}")
        except FileNotFoundError:
            print(f"[ERROR] Enemy stats file not found: {csv_path}")
            cls._stats_loaded = False
        except Exception as e:
            print(f"[ERROR] Failed to load enemy stats: {e}")
            cls._stats_loaded = False
    
    @classmethod
    def load_boss_stats(cls):
        """ボス設定をCSVファイルから読み込む"""
        if cls._boss_stats_loaded:
            return
            
        csv_path = resource_path("data/boss_stats.csv")
        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    no = int(row['No'])  # 一意のNoをキーとして使用
                    type_id = int(row['type'])
                    level = int(row['level'])
                    spawn_time = int(row['spawn_time'])
                    # Noをプライマリキー、(type, level, spawn_time)をセカンダリキーとして両方保存
                    boss_config = {
                        'no': no,
                        'type': type_id,
                        'level': level,
                        'base_hp': int(row['base_hp']),
                        'base_speed': float(row['base_speed']),
                        'base_damage': int(row['base_damage']),
                        'speed_multiplier': float(row['speed_multiplier']),
                        'attack_cooldown': int(row['attack_cooldown']),
                        'spawn_time': spawn_time,  # 出現時間（秒）
                        'image_file': row['image_file'],
                        'image_size': int(row['image_size']),
                        'projectile_speed': float(row['projectile_speed']) if row['projectile_speed'] else 3.0,
                        'description': row['description']
                    }
                    # Noベースとキーベースの両方で保存
                    cls._boss_stats[no] = boss_config  # Noベース（プライマリ）
                    key = (type_id, level, spawn_time)
                    cls._boss_stats[key] = boss_config  # 従来キーベース（互換性用）
            cls._boss_stats_loaded = True
            total_entries = len([k for k in cls._boss_stats.keys() if isinstance(k, int)])
            print(f"[INFO] Loaded {total_entries} boss configurations (No-based) from {csv_path}")
            
            # デバッグ: 読み込まれたボス設定を表示
            for no, config in cls._boss_stats.items():
                if isinstance(no, int):  # Noベースのエントリのみ表示
                    print(f"[DEBUG] Boss No.{no}: type={config['type']}, image_file={config['image_file']}, image_size={config['image_size']}, spawn_time={config['spawn_time']}s")
        except FileNotFoundError:
            print(f"[ERROR] Boss stats file not found: {csv_path}")
            cls._boss_stats_loaded = False
        except Exception as e:
            print(f"[ERROR] Failed to load boss stats: {e}")
            cls._boss_stats_loaded = False
    
    @classmethod
    def get_boss_config(cls, boss_level):
        """（非推奨）指定されたレベルのボス設定を取得（旧版・互換性用）"""
        # cls.load_boss_stats()
        # key = (101, boss_level)  # ボスタイプは101固定
        # return cls._boss_stats.get(key, None)
        return None  # 今後は使わない

    @classmethod
    def get_boss_config_by_type(cls, boss_type):
        """（削除済み）Typeベースのボス設定取得は廃止。Noベース検索を使用してください。"""
        print(f"[WARNING] get_boss_config_by_type() is deprecated. Use No-based lookup instead.")
        return None
    
    @classmethod
    def get_all_boss_configs(cls):
        """全てのボス設定を取得（行ごと）"""
        cls.load_boss_stats()
        return cls._boss_stats.copy()
    
    @classmethod
    def _load_enemy_image(cls, enemy_no, level_or_behavior, image_file_override=None, boss_no=None):
        """敵の画像を読み込む（キャッシュ機能付き）"""
        if enemy_no >= 101:
            cls.load_boss_stats()
            boss_config = None
            
            # boss_no（一意のNo）が指定されている場合はそれを優先
            if boss_no is not None:
                boss_config = cls._boss_stats.get(boss_no)
                if boss_config:
                    print(f"[DEBUG] Found boss config by No {boss_no}: image_size={boss_config['image_size']}")
                else:
                    print(f"[WARNING] Boss config not found for No {boss_no}")
            
            # フォールバック: エラー回避用のデフォルト設定
            if boss_config is None:
                print(f"[ERROR] Boss image config not found for boss_no={boss_no}, enemy_no={enemy_no}. Using default values.")
                # デフォルト設定を使用
                boss_config = {
                    'image_file': 'boss-01',
                    'image_size': 64
                }

            if boss_config:
                image_file = (image_file_override if image_file_override else boss_config['image_file']) + '.png'
                image_size = boss_config['image_size']
                # キャッシュキーをNoベースに変更（同じ画像でもサイズが異なる場合があるため）
                cache_key = f"boss-{boss_no}-{image_file_override if image_file_override else boss_config['image_file']}" if boss_no is not None else f"boss-default-{image_file_override if image_file_override else boss_config['image_file']}"
            else:
                cache_key = f"boss-{level_or_behavior:02d}"
                image_file = f"{cache_key}.png"
                image_size = 96

        else:
            cls.load_enemy_stats()
            
            # enemy_no が直接指定されている場合のみ対応
            if enemy_no in cls._enemy_stats:
                enemy_data = cls._enemy_stats[enemy_no]
                image_file = enemy_data['image_file'] + '.png'
                image_size = enemy_data['image_size']
                cache_key = f"no{enemy_no}-{enemy_data['image_file']}"
            else:
                # enemy_noが見つからない場合はエラー
                print(f"[ERROR] Enemy No.{enemy_no} not found in enemy_stats.csv")
                cls._image_cache[f"error-{enemy_no}"] = None
                return None

        if cache_key in cls._image_cache:
            # print(f"[DEBUG] Cache hit for key: {cache_key}")
            return cls._image_cache[cache_key]

        image_path = resource_path(os.path.join("assets", "character", "enemy", image_file))
        try:
            if not os.path.exists(image_path):
                print(f"[WARNING] Enemy image file not found: {image_path}")
                cls._image_cache[cache_key] = None
                return None

            image = pygame.image.load(image_path).convert_alpha()
            image = pygame.transform.scale(image, (image_size, image_size))
            image = cls._adjust_hsv(image, ENEMY_IMAGE_HUE_SHIFT, ENEMY_IMAGE_SATURATION, ENEMY_IMAGE_VALUE)
            flipped_image = pygame.transform.flip(image, True, False)

            cls._image_cache[cache_key] = {
                'left': image,
                'right': flipped_image,
                'size': image_size
            }

            # ボス画像の場合、オーラ描画用のサーフェスを事前生成してキャッシュ
            try:
                if enemy_no >= 101:
                    # 元画像のアルファマスクを作成
                    alpha_mask = pygame.mask.from_surface(image)
                    aura_thickness = 3
                    aura_offset = 2
                    aura_size = image_size + (aura_thickness + aura_offset) * 2
                    aura_surface = pygame.Surface((aura_size, aura_size), pygame.SRCALPHA)
                    red_color = (255, 50, 50, 180)
                    center_offset = (aura_thickness + aura_offset)
                    offsets = [
                        (-aura_thickness, -aura_thickness),
                        (0, -aura_thickness),
                        (aura_thickness, -aura_thickness),
                        (-aura_thickness, 0),
                        (aura_thickness, 0),
                        (-aura_thickness, aura_thickness),
                        (0, aura_thickness),
                        (aura_thickness, aura_thickness)
                    ]
                    for dx, dy in offsets:
                        outline_pos = (center_offset + dx, center_offset + dy)
                        for point in alpha_mask.outline():
                            x, y = point
                            # 小さい円でアウトラインを描画（1px）
                            pygame.draw.circle(aura_surface, red_color, (x + outline_pos[0], y + outline_pos[1]), 1)

                    cls._image_cache[cache_key]['aura'] = aura_surface
            except Exception:
                # オーラ生成に失敗しても読み込み自体は成功させる
                pass

            # print(f"[DEBUG] Loaded image for key: {cache_key}, file: {image_file}")
            return cls._image_cache[cache_key]

        except (pygame.error, FileNotFoundError) as e:
            print(f"[WARNING] Failed to load enemy image {cache_key}: {e}")
            cls._image_cache[cache_key] = None
            return None
        except Exception as e:
            print(f"[ERROR] Unexpected error loading enemy image {cache_key}: {e}")
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
    
    def __init__(self, screen, game_time, spawn_x=None, spawn_y=None, spawn_side=None, is_boss=False, boss_level=1, boss_type=None, boss_image_file=None, boss_stats_key=None, boss_no=None, enemy_no=None):
        self.screen = screen
        self.is_boss = is_boss  # ボス判定フラグ
        self.boss_level = boss_level if is_boss else 1  # ボスレベル（ボス以外は1）
        self.boss_type = boss_type if boss_type is not None else 101  # ボスタイプ（デフォルトは101）
        self.boss_image_file = boss_image_file  # ボス画像ファイル名（mainから渡す）
        self.boss_stats_key = boss_stats_key  # ボス設定キー（mainから渡す）
        self.boss_no = boss_no  # ボス番号（CSVのNoカラム）
        self.enemy_no = enemy_no  # 通常敵の番号（CSVのenemy_noカラム）
        
        # ヒット時のフラッシュ用タイマ（秒）
        self.hit_flash_timer = 0.0
        self.hit_flash_duration = 0.25  # フェードイン+フェードアウトの合計時間
        
        # デバッグフラグ（サイズ情報の重複ログを防ぐ）
        self._debug_size_logged = False
        
        # 全体的にやや遅めに調整
        # base_speed を導入して、プレイヤーの speed 変更の影響を受けないようにする
        self.base_speed = 1.5
        self.speed = self.base_speed
        
        # ボスか通常敵かで敵タイプを決定
        if self.is_boss:
            # ボスタイプ（101以上）
            self.enemy_type = self.boss_type  # boss_typeを使用
            # ボスタイプに応じて行動パターンを設定
            if self.boss_type == 101:
                self.behavior_type = 1  # 追跡タイプ
            elif self.boss_type == 102:
                self.behavior_type = 2  # 直進タイプ
            elif self.boss_type == 103:
                self.behavior_type = 3  # 距離保持射撃タイプ
            elif self.boss_type == 104:
                self.behavior_type = 4  # プレイヤーに近づきながら射撃
            else:
                self.behavior_type = 1  # デフォルトは追跡
            self.level = 1  # ボスのレベルは1固定（タイプで区別）
        else:
            # 通常敵：enemy_noが必須
            if self.enemy_no is None:
                raise ValueError("enemy_no is required for normal enemies")
            
            Enemy.load_enemy_stats()
            if self.enemy_no not in self._enemy_stats:
                raise ValueError(f"Enemy No.{self.enemy_no} not found in enemy_stats.csv")
            
            enemy_data = self._enemy_stats[self.enemy_no]
            self.behavior_type = enemy_data['type']
            self.level = enemy_data['level']
            self.enemy_type = self.behavior_type  # typeと同じ値
        
        # 行動パターン用の変数
        self.initial_direction = None  # 直進タイプ用の初期方向
        self.target_distance = 200  # 距離保持タイプ用の目標距離（倍に拡大）
        self.attack_cooldown = 0  # 攻撃クールダウン（ミリ秒）
        self.last_attack_time = 0  # 最後の攻撃時刻
        self.projectiles = []  # 敵が発射した弾丸
        
        # 跳ね返りタイプ（タイプ2）用の変数
        self.velocity_x = 0  # X方向の速度
        self.velocity_y = 0  # Y方向の速度
        self.bounces_remaining = 5  # 残り跳ね返り回数（無限にしたい場合は大きな値）
        
        # 生存時間管理
        self.spawn_time = pygame.time.get_ticks()  # 生成時刻
        
        # 歩行アニメーション用変数
        self.animation_time = 0.0  # アニメーション用タイマー
        self.is_moving = False     # 移動しているかどうか
        self.last_x = self.x if hasattr(self, 'x') else 0
        self.last_y = self.y if hasattr(self, 'y') else 0
        
        # 描画用変数
        self.facing_right = True  # 敵の向き（右向きかどうか）
        
        # ノックバック関連の変数
        self.knockback_velocity_x = 0.0  # ノックバック速度X
        self.knockback_velocity_y = 0.0  # ノックバック速度Y
        self.knockback_timer = 0.0       # ノックバック残り時間（秒）
        self.knockback_duration = KNOCKBACK_DURATION    # ノックバック持続時間（秒）
        self.knockback_cooldown = 0.0    # ノックバッククールダウン残り時間
        self.knockback_cooldown_duration = KNOCKBACK_COOLDOWN_DURATION  # ノックバック後のクールダウン時間
        
        # 敵のタイプに応じてステータスを設定
        self.setup_enemy_stats()
        
        # スポーン位置の指定があればそれを使う（main からカメラ外座標を渡せる）
        if spawn_x is not None and spawn_y is not None:
            # 明示的なワールド座標を使用
            self.x = spawn_x
            self.y = spawn_y
            # ワールド内にスポーンした場合は障害物チェック
            self._adjust_spawn_position()
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
    
    def _adjust_spawn_position(self):
        """スポーン位置が障害物と重なっている場合、近くの通行可能な場所に移動"""
        if not USE_CSV_MAP:
            return
        
        try:
            from ui.stage import get_stage_map
            stage_map = get_stage_map()
            
            # 現在位置をチェック
            if not self._is_position_blocked(self.x, self.y, stage_map):
                return  # 問題なし
            
            # 周囲の通行可能な位置を探す
            search_radius = 100
            attempts = 50
            
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
                    if not self._is_position_blocked(new_x, new_y, stage_map):
                        self.x = new_x
                        self.y = new_y
                        return
            
            # 適切な位置が見つからない場合は、ワールド外に移動
            self.x = -50
            self.y = random.randint(0, WORLD_HEIGHT)
            
        except Exception:
            # エラーが発生した場合は位置調整をスキップ
            pass
    
    def _is_position_blocked(self, x, y, stage_map):
        """指定座標が障害物でブロックされているかチェック"""
        # エネミーの四隅をチェック
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

    @classmethod
    def get_random_enemy_no(cls, game_time):
        """時間に応じてランダムなenemy_noを選択する（新方式）"""
        cls.load_enemy_stats()
        
        # 現在利用可能なenemy_noのリストを取得
        available_enemies = list(cls._enemy_stats.keys())
        if not available_enemies:
            return 1  # フォールバック
        
        # 時間に応じた重み付け選択
        if game_time <= 30:  # 序盤（0-30秒）
            # レベル1の敵を優先
            candidates = [no for no in available_enemies 
                         if cls._enemy_stats[no]['level'] == 1]
            if candidates:
                return random.choice(candidates)
            
        elif game_time <= 70:  # 中盤（31-70秒）
            # レベル1-2の敵を中心に、一部レベル3も
            weights = []
            candidates = []
            for no in available_enemies:
                level = cls._enemy_stats[no]['level']
                if level == 1:
                    weight = 0.5  # 50%
                elif level == 2:
                    weight = 0.3  # 30%
                elif level == 3:
                    weight = 0.2  # 20%
                else:
                    weight = 0.0  # 登場しない
                
                if weight > 0:
                    candidates.append(no)
                    weights.append(weight)
            
            if candidates:
                return random.choices(candidates, weights=weights)[0]
                
        else:  # 終盤（71秒以降）
            # 全レベルが出現、高レベルの確率が上昇
            weights = []
            candidates = []
            for no in available_enemies:
                level = cls._enemy_stats[no]['level']
                if level == 1:
                    weight = 0.25  # 25%
                elif level == 2:
                    weight = 0.25  # 25%
                elif level == 3:
                    weight = 0.25  # 25%
                elif level == 4:
                    weight = 0.15  # 15%
                elif level == 5:
                    weight = 0.10  # 10%
                else:
                    weight = 0.0
                
                if weight > 0:
                    candidates.append(no)
                    weights.append(weight)
            
            if candidates:
                return random.choices(candidates, weights=weights)[0]
        
        # フォールバック：最初の敵
        return available_enemies[0]

    def setup_enemy_stats(self):
        # ボスの場合はボス設定から読み込み
        if self.is_boss:
            Enemy.load_boss_stats()
            boss_config = None
            
            # boss_no（一意のNo）が指定されている場合はそれを優先
            if self.boss_no is not None:
                boss_config = Enemy._boss_stats.get(self.boss_no)
                if boss_config:
                    print(f"[DEBUG] Found boss config by No {self.boss_no}: type={boss_config['type']}, image_size={boss_config['image_size']}")
                else:
                    print(f"[WARNING] Boss config not found for No {self.boss_no}")
            
            # フォールバック1: boss_stats_keyによる検索
            if boss_config is None and self.boss_stats_key:
                boss_config = Enemy._boss_stats.get(self.boss_stats_key)
                if boss_config:
                    print(f"[DEBUG] Found boss config by stats_key {self.boss_stats_key}: image_size={boss_config['image_size']}")
            
            # フォールバック2: デフォルト設定（エラー回避用）
            if boss_config is None:
                print(f"[ERROR] Boss config not found for boss_no={self.boss_no}, boss_type={self.boss_type}. Using default values.")
                # デフォルト設定を作成
                boss_config = {
                    'base_hp': 100,
                    'base_speed': 1.0,
                    'base_damage': 20,
                    'speed_multiplier': 1.2,
                    'attack_cooldown': 1000,
                    'projectile_speed': 2.0,
                    'image_size': 64,  # デフォルトサイズ
                    'image_file': 'boss-01'  # デフォルト画像
                }
            
            if boss_config:
                # ボス設定から直接ステータスを設定
                self.hp = boss_config['base_hp']
                self.max_hp = boss_config['base_hp']  # 最大HPを記録
                self.base_speed = boss_config['base_speed'] * boss_config['speed_multiplier']
                self.damage = boss_config['base_damage']
                self.attack_cooldown = boss_config['attack_cooldown']
                self.projectile_speed = boss_config['projectile_speed']
                
                # ボス用サイズ設定
                image_size = boss_config['image_size']
                self.size = int(image_size * 0.7)  # 画像サイズの70%
                
                # ボス用の色設定（金色）
                self.color = (255, 215, 0)  # ゴールド
                
                # ボス用のスピード設定
                self.speed = self.base_speed
                
                # ボスタイプに応じた行動パターンを設定
                if self.boss_type == 101:
                    self.behavior_type = 1  # 追跡
                elif self.boss_type == 102:
                    self.behavior_type = 2  # 直進
                elif self.boss_type == 103:
                    self.behavior_type = 3  # 距離保持射撃
                elif self.boss_type == 104:
                    self.behavior_type = 4  # ランダム移動
                else:
                    self.behavior_type = 1  # デフォルトは追跡
                
                # ボス画像の読み込み
                try:
                    image_file_for_cache = self.boss_image_file if self.boss_image_file else boss_config['image_file']
                    print(f"[DEBUG] Loading boss image: boss_no={self.boss_no}, boss_type={self.boss_type}, image_file={image_file_for_cache}, expected_size={boss_config['image_size']}")
                    self.images = self._load_enemy_image(self.enemy_type, self.level, image_file_for_cache, boss_no=self.boss_no)
                    if self.images is None:
                        print(f"[WARNING] Failed to load boss image, using fallback")
                        self.images = None
                    else:
                        print(f"[DEBUG] Boss image loaded successfully: cached_size={self.images.get('size', 'unknown')}")
                except Exception as e:
                    print(f"[ERROR] Exception while loading boss image: {e}")
                    self.images = None
                return
        
        # 通常エネミーの場合はエネミー設定から読み込み
        Enemy.load_enemy_stats()
        
        # enemy_noが必須：指定されていない場合はエラー
        if not hasattr(self, 'enemy_no') or self.enemy_no is None:
            raise ValueError("enemy_no is required for normal enemies")
        
        # ステータス取得
        if self.enemy_no not in self._enemy_stats:
            raise ValueError(f"Enemy No.{self.enemy_no} not found in enemy_stats.csv")
            
        stats = self._enemy_stats[self.enemy_no]
        
        # 基本ステータス設定
        self.hp = stats['base_hp']
        self.max_hp = stats['base_hp']  # 最大HPを記録
        self.base_speed = stats['base_speed'] * stats['speed_multiplier']
        self.damage = stats['base_damage']
        self.attack_cooldown = stats['attack_cooldown']
        self.projectile_speed = stats.get('projectile_speed', 2.0)  # デフォルト値2.0
        
        # CSVからサイズ情報を取得（当たり判定用）
        image_size = stats['image_size']
        # 当たり判定は画像サイズより少し小さめに設定
        self.size = int(image_size * 0.7)  # 画像サイズの70%
        
        # 行動パターンに応じた色設定（レベルに応じて彩度を変える）
        if self.is_boss:
            # ボス専用の色（金色/黄色）
            self.color = self._hsv_to_rgb(50.0, 0.8, 220)  # 金色
        else:
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
        
        self.speed = self.base_speed
        
        # 画像の読み込み（エラーハンドリング強化）
        try:
            if self.is_boss:
                # ボスの場合は従来の方式
                level_or_behavior = self.boss_level
                self.images = self._load_enemy_image(self.enemy_type, level_or_behavior)
            else:
                # 通常敵の場合はenemy_noを使用
                self.images = self._load_enemy_image(self.enemy_no, 0)  # level_or_behaviorは使わない
            
            # 画像読み込みに失敗した場合のフォールバック
            if self.images is None:
                print(f"[WARNING] Failed to load enemy image for enemy_no {getattr(self, 'enemy_no', 'unknown')}, using fallback")
                self.images = None
        except Exception as e:
            print(f"[ERROR] Exception while loading enemy image: {e}")
            self.images = None
            
        # images属性が設定されていない場合の安全対策
        if not hasattr(self, 'images'):
            print(f"[ERROR] images attribute not set, initializing to None")
            self.images = None
            
        self.facing_right = True  # 向いている方向（True: 右, False: 左）
        self.last_movement_x = 0  # 最後の移動方向を記録

    def apply_knockback(self, attack_x, attack_y, knockback_force):
        """ノックバックを適用する
        
        Args:
            attack_x (float): 攻撃位置X
            attack_y (float): 攻撃位置Y
            knockback_force (float): ノックバックの力
        """
        # クールダウン中はノックバックしない
        if self.knockback_cooldown > 0:
            return
            
        # 攻撃位置から敵への方向を計算
        dx = self.x - attack_x
        dy = self.y - attack_y
        distance = math.sqrt(dx**2 + dy**2)
        
        # ゼロ除算を回避
        if distance == 0:
            dx, dy = 1, 0  # デフォルト方向（右）
            distance = 1
        
        # 短時間で同じ距離のノックバック
        enhanced_force = knockback_force * 1.5  # 力を1.5倍に戻す（距離を維持）
        
        # 正規化してノックバック速度を設定
        self.knockback_velocity_x = (dx / distance) * enhanced_force
        self.knockback_velocity_y = (dy / distance) * enhanced_force
        self.knockback_timer = self.knockback_duration

    def update_knockback(self, dt=1/60):
        """ノックバックの更新処理"""
        # ノックバック処理
        if self.knockback_timer > 0:
            # ノックバック移動を適用
            potential_x = self.x + self.knockback_velocity_x * dt
            potential_y = self.y + self.knockback_velocity_y * dt
            
            # 障害物チェック（stage_mapを取得）
            blocked = False
            if USE_CSV_MAP:
                try:
                    from ui.stage import get_stage_map
                    stage_map = get_stage_map()
                    blocked = self._is_position_blocked(potential_x, potential_y, stage_map)
                except Exception:
                    blocked = False
            
            if not blocked:
                self.x = potential_x
                self.y = potential_y
            
            # ノックバック時間を減らす
            self.knockback_timer -= dt
            
            # ノックバック終了時にクールダウンを開始
            if self.knockback_timer <= 0:
                self.knockback_velocity_x = 0
                self.knockback_velocity_y = 0
                self.knockback_timer = 0
                self.knockback_cooldown = self.knockback_cooldown_duration  # クールダウン開始
        
        # クールダウンタイマーの更新
        if self.knockback_cooldown > 0:
            self.knockback_cooldown -= dt
            if self.knockback_cooldown < 0:
                self.knockback_cooldown = 0

    def move(self, player, camera_x=0, camera_y=0, map_loader=None, enemies=None, delta_time=1.0):
        """行動パターンに応じた移動処理"""
        # ノックバック中のみ通常の移動を無効にする（クールダウン中は移動可能）
        if self.knockback_timer > 0:
            return
            
        new_x, new_y = self.x, self.y
        
        if self.behavior_type == 1:
            # 1. プレイヤーに寄ってくる（追跡）
            angle = math.atan2(player.y - self.y, player.x - self.x)
            new_x = self.x + math.cos(angle) * self.base_speed * delta_time
            new_y = self.y + math.sin(angle) * self.base_speed * delta_time
            
        elif self.behavior_type == 2:
            # 2. 直進タイプ（プレイヤー方向へ一直線に進み、画面外に出ていく）
            # ここでは跳ね返りや地形反転を行わず、軽量に直進させる
            if self.initial_direction is None:
                # 初回のみプレイヤー方向を計算して保存し、速度ベクトルを設定
                self.initial_direction = math.atan2(player.y - self.y, player.x - self.x)
                self.velocity_x = math.cos(self.initial_direction) * self.base_speed
                self.velocity_y = math.sin(self.initial_direction) * self.base_speed

            # 速度ベクトルによる移動（反転処理は行わない）（delta_timeを適用）
            new_x = self.x + self.velocity_x * delta_time
            new_y = self.y + self.velocity_y * delta_time
            
        elif self.behavior_type == 3:
            # 3. プレイヤーから一定の距離を保ち、魔法の杖のような弾を発射する
            distance_to_player = math.hypot(player.x - self.x, player.y - self.y)
            
            if distance_to_player < self.target_distance - 20:
                # プレイヤーに近すぎる場合は離れる（許容範囲も倍に）
                angle = math.atan2(self.y - player.y, self.x - player.x)  # プレイヤーから離れる方向
                new_x = self.x + math.cos(angle) * self.base_speed * delta_time
                new_y = self.y + math.sin(angle) * self.base_speed * delta_time
            elif distance_to_player > self.target_distance + 20:
                # プレイヤーから遠すぎる場合は近づく（許容範囲も倍に）
                angle = math.atan2(player.y - self.y, player.x - self.x)  # プレイヤーに向かう方向
                new_x = self.x + math.cos(angle) * self.base_speed * delta_time
                new_y = self.y + math.sin(angle) * self.base_speed * delta_time
            # 適切な距離の場合は移動しない
            
        elif self.behavior_type == 4:
            # 4. プレイヤーに近づきながら射撃攻撃
            angle = math.atan2(player.y - self.y, player.x - self.x)
            new_x = self.x + math.cos(angle) * self.base_speed * delta_time
            new_y = self.y + math.sin(angle) * self.base_speed * delta_time
        
        # 敵同士の衝突回避ヘルパー
        def _would_collide_with_others(px, py, enemies_list):
            if not enemies_list:
                return False
            for other in enemies_list:
                if other is self:
                    continue
                # 同期的に削除対象や無効なエネミーは無視
                if not hasattr(other, 'x') or not hasattr(other, 'y'):
                    continue
                # 距離で単純判定（中心間距離 < 半径和 * factor）
                from constants import ENEMY_COLLISION_SEPARATION_FACTOR
                factor = float(ENEMY_COLLISION_SEPARATION_FACTOR)
                min_dist = (self.size + getattr(other, 'size', 0)) * factor
                dx = px - other.x
                dy = py - other.y
                if dx * dx + dy * dy < (min_dist * min_dist):
                    return True
            return False

        # 障害物との衝突判定（CSVマップまたはステージマップが有効な場合）
        if USE_CSV_MAP and (new_x != self.x or new_y != self.y):
            try:
                from ui.stage import get_stage_map
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
                    # 分離処理の可否を確認。無効なら古いフォールバック処理のみ実行する
                    separation_skipped = False
                    from constants import ENABLE_ENEMY_SEPARATION
                    separation_enabled = bool(ENABLE_ENEMY_SEPARATION)

                    if not separation_enabled:
                        # フォールバックのみ実行
                        if _would_collide_with_others(new_x, new_y, enemies):
                            if not _would_collide_with_others(new_x, self.y, enemies):
                                self.x = new_x
                            elif not _would_collide_with_others(self.x, new_y, enemies):
                                self.y = new_y
                            else:
                                pass
                        else:
                            self.x = new_x
                            self.y = new_y
                        separation_skipped = True

                    # 分離ベクトルによるやさしい押しのけ処理
                    if not separation_skipped:
                        from constants import ENEMY_SEPARATION_STRENGTH, ENEMY_SEPARATION_BOSS_PRIORITY, ENEMY_COLLISION_SEPARATION_FACTOR
                        sep_strength = float(ENEMY_SEPARATION_STRENGTH)
                        boss_priority = float(ENEMY_SEPARATION_BOSS_PRIORITY)
                        factor = float(ENEMY_COLLISION_SEPARATION_FACTOR)

                        sep_x = 0.0
                        sep_y = 0.0
                        total_w = 0.0
                        if enemies:
                            for other in enemies:
                                if other is self:
                                    continue
                                if not hasattr(other, 'x') or not hasattr(other, 'y'):
                                    continue
                                dx_o = new_x - other.x
                                dy_o = new_y - other.y
                                # 距離の二乗で比較して sqrt を避ける
                                dist2 = dx_o * dx_o + dy_o * dy_o
                                desired = (self.size + getattr(other, 'size', 0)) * factor
                                desired2 = desired * desired
                                if dist2 <= 0:
                                    # 完全一致のときは小さなランダム方向で押しのけ
                                    nx, ny = 1.0, 0.0
                                    overlap = desired
                                else:
                                    if dist2 >= desired2:
                                        continue
                                    dist = math.sqrt(dist2)
                                    nx = dx_o / dist
                                    ny = dy_o / dist
                                    overlap = (desired - dist)

                            # 重み: 重なりの割合
                            w = (overlap / max(1.0, desired))
                            # ボス優先: 他がボスで自分が非ボスなら強めに押しのける
                            if getattr(other, 'is_boss', False) and not getattr(self, 'is_boss', False):
                                w *= boss_priority
                            # ボスは他からの押しを受けにくくする（自分がボスの場合は弱める）
                            if getattr(self, 'is_boss', False) and not getattr(other, 'is_boss', False):
                                w *= 0.6

                            sep_x += nx * w
                            sep_y += ny * w
                            total_w += w

                    applied = False
                    if total_w > 0.0:
                        mag = math.hypot(sep_x, sep_y)
                        if mag > 0.0:
                            # 最大押し量は base_speed * sep_strength
                            max_push = self.base_speed * sep_strength
                            push_x = (sep_x / mag) * max_push
                            push_y = (sep_y / mag) * max_push
                            cand_x = new_x + push_x
                            cand_y = new_y + push_y

                            # 候補位置が地形・他エネミーと衝突しないか確認
                            valid_candidate = True
                            if USE_CSV_MAP:
                                from ui.stage import get_stage_map
                                stage_map = get_stage_map()
                                half_size = self.size // 2
                                check_points = [
                                    (cand_x - half_size, cand_y - half_size),
                                    (cand_x + half_size, cand_y - half_size),
                                    (cand_x - half_size, cand_y + half_size),
                                    (cand_x + half_size, cand_y + half_size),
                                    (cand_x, cand_y)
                                ]
                                for cx, cy in check_points:
                                    tile_id = map_loader.get_tile_at(cx, cy) if map_loader else stage_map.get_tile_at(cx, cy)
                                    if tile_id in {5,7,8,9}:
                                        valid_candidate = False
                                        break
                            # 他エネミーとの衝突
                            if valid_candidate and _would_collide_with_others(cand_x, cand_y, enemies):
                                valid_candidate = False

                            if valid_candidate:
                                self.x = cand_x
                                self.y = cand_y
                                applied = True

                    if not applied:
                        # 既存のフォールバック: Xのみ/Yのみ/移動キャンセル
                        if _would_collide_with_others(new_x, new_y, enemies):
                            if not _would_collide_with_others(new_x, self.y, enemies):
                                self.x = new_x
                            elif not _would_collide_with_others(self.x, new_y, enemies):
                                self.y = new_y
                            else:
                                pass
                        else:
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
                                # 同様にY移動を適用する前に他の敵との重なりをチェック
                                if not _would_collide_with_others(self.x, new_y, enemies):
                                    self.y = new_y
            
            except Exception:
                # 障害物判定に失敗した場合は通常の移動
                self.x = new_x
                self.y = new_y
        else:
            # マップが無効な場合は障害物判定なしで移動
            if _would_collide_with_others(new_x, new_y, enemies):
                # Xのみを試す
                if not _would_collide_with_others(new_x, self.y, enemies):
                    self.x = new_x
                elif not _would_collide_with_others(self.x, new_y, enemies):
                    self.y = new_y
                else:
                    # どちらもダメなら移動をキャンセル
                    pass
            else:
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
        if (hasattr(self, 'images') and self.images and isinstance(self.images, dict) and 
            'right' in self.images and 'left' in self.images and
            self.images['right'] is not None and self.images['left'] is not None):
            
            # 向きに応じて画像を選択
            image = self.images['right'] if self.facing_right else self.images['left']
            
            # 画像が正常に取得できた場合のみ描画
            if image is not None:
                # 画像のサイズを取得（実際の画像サイズを優先、フォールバックとしてキャッシュのサイズ情報を使用）
                actual_image_size = image.get_width()  # 実際にスケールされた画像のサイズ
                cached_size = self.images.get('size', 32)
                image_size = actual_image_size if actual_image_size > 0 else cached_size
                
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
                
                # ボス用の赤いオーラ効果（enemy_typeが101以上の場合のみ）
                if hasattr(self, 'enemy_type') and self.enemy_type >= 101:
                    self._draw_boss_aura(screen, base_x, base_y, current_image, image_size)
                
                # ボス用のHPバー（enemy_typeが101以上の場合のみ）
                if hasattr(self, 'enemy_type') and self.enemy_type >= 101:
                    self._draw_boss_hp_bar(screen, sx, sy, image_size)
                
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
        # ボス用の赤いオーラ（円形の場合、enemy_typeが101以上の場合のみ）
        if hasattr(self, 'enemy_type') and self.enemy_type >= 101:
            aura_radius = self.size + 6
            aura_color = (255, 50, 50, 100)  # 赤色、透明
            aura_surface = pygame.Surface((aura_radius*2, aura_radius*2), pygame.SRCALPHA)
            pygame.draw.circle(aura_surface, aura_color, (aura_radius, aura_radius), aura_radius, 3)
            screen.blit(aura_surface, (sx - aura_radius, sy - aura_radius))
        
        # ボス用のHPバー（円形の場合、enemy_typeが101以上の場合のみ）
        if hasattr(self, 'enemy_type') and self.enemy_type >= 101:
            self._draw_boss_hp_bar(screen, sx, sy, self.size * 2)
        
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
        elif self.behavior_type == 4:  # 近接射撃 - 星マーク
            # プレイヤーに近づきながら射撃することを表す星マーク
            star_points = []
            for i in range(8):
                angle = i * math.pi / 4
                if i % 2 == 0:
                    radius = icon_size
                else:
                    radius = icon_size // 2
                x = sx + radius * math.cos(angle)
                y = sy + icon_y_offset + radius * math.sin(angle)
                star_points.append((x, y))
            pygame.draw.polygon(screen, (255, 255, 255), star_points)

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
            # ボスの弾かどうかを判定
            is_boss = hasattr(self, 'enemy_type') and self.enemy_type >= 101
            
            # 通常エネミーの弾丸数制限（ボスは制限なし）
            if not is_boss and len(self.projectiles) >= 5:
                # 古い弾丸を削除
                self.projectiles.pop(0)
            
            projectile = EnemyProjectile(self.x, self.y, angle, self.damage // 2, self.behavior_type, self.enemy_type, is_boss_bullet=is_boss, projectile_speed=self.projectile_speed)
            self.projectiles.append(projectile)
            self.last_attack_time = current_time

    def update_projectiles(self, player=None, delta_time=1.0):
        """弾丸の更新処理"""
        # 有効期限切れや画面外の弾丸を削除
        valid_projectiles = []
        for p in self.projectiles:
            if p.is_expired() or not p.is_on_screen():
                continue
            
            # プレイヤーから遠い弾丸も削除（パフォーマンス向上、ボスの弾は除外）
            if player is not None and not p.is_boss_bullet:
                dx = p.x - player.x
                dy = p.y - player.y
                # 通常の弾は600ピクセル、ボスの弾は制限なし
                max_distance_sq = 360000  # 600ピクセルの二乗
                if dx * dx + dy * dy > max_distance_sq:
                    continue
                    continue
            
            valid_projectiles.append(p)
        
        self.projectiles = valid_projectiles
        
        # 弾丸の移動（delta_timeを渡す）
        for projectile in self.projectiles:
            projectile.update(delta_time)

    def draw_projectiles(self, screen, camera_x=0, camera_y=0):
        """弾丸の描画"""
        for projectile in self.projectiles:
            projectile.draw(screen, camera_x, camera_y)

    def get_projectiles(self):
        """弾丸のリストを取得（プレイヤーとの衝突判定用）"""
        return self.projectiles

    def is_off_screen(self):
        """敵が画面外に出たかどうかを判定（直進タイプ用）"""
        # ボスは画面外でも削除されない
        if self.is_boss:
            return False
            
        margin = 100
        return (self.x < -margin or self.x > WORLD_WIDTH + margin or 
                self.y < -margin or self.y > WORLD_HEIGHT + margin)

    def is_boss_off_screen(self):
        """ボスが画面外に出たかどうかを判定（リスポーン用）"""
        if not self.is_boss:
            return False
            
        return (self.x < -BOSS_WORLD_MARGIN or self.x > WORLD_WIDTH + BOSS_WORLD_MARGIN or 
                self.y < -BOSS_WORLD_MARGIN or self.y > WORLD_HEIGHT + BOSS_WORLD_MARGIN)

    def respawn_boss_randomly(self, player):
        """ボスをランダムな位置にリスポーン（HPは維持）"""
        if not self.is_boss:
            return
            
        # 画面外からランダムにスポーン
        screen_margin = 100
        side = random.randint(0, 3)  # 0:上, 1:右, 2:下, 3:左
        
        if side == 0:  # 上から
            self.x = player.x + random.randint(-SCREEN_WIDTH//2, SCREEN_WIDTH//2)
            self.y = player.y - SCREEN_HEIGHT//2 - screen_margin
        elif side == 1:  # 右から
            self.x = player.x + SCREEN_WIDTH//2 + screen_margin
            self.y = player.y + random.randint(-SCREEN_HEIGHT//2, SCREEN_HEIGHT//2)
        elif side == 2:  # 下から
            self.x = player.x + random.randint(-SCREEN_WIDTH//2, SCREEN_WIDTH//2)
            self.y = player.y + SCREEN_HEIGHT//2 + screen_margin
        else:  # 左から
            self.x = player.x - SCREEN_WIDTH//2 - screen_margin
            self.y = player.y + random.randint(-SCREEN_HEIGHT//2, SCREEN_HEIGHT//2)
        
        # ワールド境界をクランプ
        self.x = max(50, min(WORLD_WIDTH - 50, self.x))
        self.y = max(50, min(WORLD_HEIGHT - 50, self.y))

    def is_far_from_player(self, player, margin=800):
        """プレイヤーから十分に離れているかどうかを判定（視界外削除用）"""
        # ボスは距離に関係なく削除されない
        if self.is_boss:
            return False
            
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
        # ボスは常に画面範囲内とみなす（削除されない）
        if self.is_boss:
            return True
            
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
        """生存時間に基づく削除判定"""
        # ボスは時間による削除もされない
        if self.is_boss:
            return False
            
        if self.behavior_type == 2:  # 跳ね返り直進
            # 跳ね返りタイプは60秒で削除（長めに設定）
            return pygame.time.get_ticks() - self.spawn_time > 60000
        elif self.behavior_type == 3:  # 距離保持射撃
            # 距離保持射撃は45秒で削除
            return pygame.time.get_ticks() - self.spawn_time > 45000
        else:
            # その他のタイプは時間制限なし
            return False

    def get_type_info(self):
        """敵の種類情報を取得（デバッグ用）"""
        behavior_names = {
            1: "追跡",
            2: "跳ね返り", 
            3: "距離保持",
            4: "近接射撃"
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

    def _draw_boss_aura(self, screen, base_x, base_y, image, image_size):
        """ボス用の赤いオーラ効果を描画（最適化版、画像ベース）"""
        # オーラキャッシュの確認（画像と向きごとにキャッシュ）
        cache_key = f"{image_size}_{self.facing_right}_{id(image)}"
        if not hasattr(self, '_aura_cache'):
            self._aura_cache = {}
        
        # キャッシュされたオーラサーフェースを使用
        if cache_key not in self._aura_cache:
            # 画像の輪郭に基づいたオーラを作成（初回のみ）
            aura_thickness = 3
            aura_size = image_size + aura_thickness * 4
            aura_surface = pygame.Surface((aura_size, aura_size), pygame.SRCALPHA)
            
            # 元画像のアルファマスクを作成（初回のみ）
            try:
                alpha_mask = pygame.mask.from_surface(image)
                outline_points = alpha_mask.outline()
                
                if outline_points:
                    # アウトライン効果を作成（複数層で厚みを表現）
                    center_offset = aura_thickness * 2
                    red_colors = [
                        (255, 100, 100, 80),   # 外側（薄い）
                        (255, 80, 80, 120),    # 中間
                        (255, 60, 60, 160)     # 内側（濃い）
                    ]
                    
                    # 複数の厚さでアウトラインを描画
                    for thickness_idx in range(aura_thickness):
                        color = red_colors[min(thickness_idx, len(red_colors) - 1)]
                        offset_distance = aura_thickness - thickness_idx
                        
                        # 8方向にオフセットして描画
                        offsets = [
                            (-offset_distance, -offset_distance),
                            (0, -offset_distance),
                            (offset_distance, -offset_distance),
                            (-offset_distance, 0),
                            (offset_distance, 0),
                            (-offset_distance, offset_distance),
                            (0, offset_distance),
                            (offset_distance, offset_distance)
                        ]
                        
                        for dx, dy in offsets:
                            for point in outline_points:
                                x, y = point
                                pygame.draw.circle(aura_surface, color, 
                                                 (x + center_offset + dx, y + center_offset + dy), 1)
                else:
                    # アウトラインが取得できない場合は円形フォールバック
                    center = aura_size // 2
                    radius = image_size // 2 + aura_thickness
                    red_color = (255, 80, 80, 120)
                    for i in range(aura_thickness):
                        pygame.draw.circle(aura_surface, red_color, (center, center), radius - i, 1)
                        
            except Exception:
                # マスク作成に失敗した場合は円形フォールバック
                center = aura_size // 2
                radius = image_size // 2 + aura_thickness
                red_color = (255, 80, 80, 120)
                for i in range(aura_thickness):
                    pygame.draw.circle(aura_surface, red_color, (center, center), radius - i, 1)
            
            self._aura_cache[cache_key] = aura_surface
        
        # キャッシュされたオーラを描画
        aura_surface = self._aura_cache[cache_key]
        aura_offset = (aura_surface.get_width() - image_size) // 2
        screen.blit(aura_surface, (base_x - aura_offset, base_y - aura_offset))

    def _draw_boss_hp_bar(self, screen, center_x, center_y, entity_size):
        """ボス用のHPバーを描画（小型版、文字なし）"""
        bar_width = max(30, (entity_size + 20) // 2)  # 元の半分のサイズ
        bar_height = 3  # 高さも半分
        bar_x = center_x - bar_width // 2
        bar_y = center_y - entity_size // 2 - 20  # エンティティの上部に配置（より離して）
        
        # 背景バー（赤色 - 失われたHP部分）
        pygame.draw.rect(screen, (200, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        
        # HPバー（緑色 - 残りのHP部分）
        hp_ratio = max(0, self.hp / self.max_hp)
        hp_width = int(bar_width * hp_ratio)
        
        if hp_width > 0:
            # 残りのHPを緑色で表示
            hp_color = (0, 200, 0)  # 緑色
            pygame.draw.rect(screen, hp_color, (bar_x, bar_y, hp_width, bar_height))
        
        # 枠線（白）
        pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 1)


class EnemyProjectile:
    """敵が発射する弾丸クラス"""
    # 描画用のキャッシュサーフェス（クラス変数）
    _draw_cache = {}
    
    def __init__(self, x, y, angle, damage, behavior_type=3, enemy_level=1, is_boss_bullet=False, projectile_speed=2.0):
        self.x = x
        self.y = y
        self.angle = angle
        self.damage = damage
        self.behavior_type = behavior_type
        self.enemy_level = enemy_level  # 敵のレベルを記録
        self.is_boss_bullet = is_boss_bullet  # ボスの弾かどうか
        self.speed = projectile_speed  # 弾丸の速度（CSVから設定）
        self.size = 20 if not is_boss_bullet else 24  # 通常弾とボス弾のサイズ調整
        self.lifetime = 3000  # 3秒で消滅（ミリ秒）
        self.created_time = pygame.time.get_ticks()
        self.pulse_alpha = 200  # 脈動エフェクト用のアルファ値（初期化）
        
        # 通常の弾丸のサイズを視認性重視で調整
        if not is_boss_bullet:
            self.size = 22  # 18から22に拡大（より見やすく）
        
        # 速度ベクトルを計算
        self.vx = math.cos(angle) * self.speed
        self.vy = math.sin(angle) * self.speed
        
        # 敵と同じ彩度設定で弾丸の色を決定
        self._setup_bullet_color()

    def _setup_bullet_color(self):
        """敵のレベルと行動パターンに応じた弾丸の色を設定"""
        # ボスの弾は特別な色（金色、相殺不可を表現）
        if self.is_boss_bullet:
            self.base_color = (255, 215, 0)  # 金色
            return
        
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

    def update(self, delta_time=1.0):
        """弾丸の移動処理（最適化版）"""
        self.x += self.vx * delta_time
        self.y += self.vy * delta_time
        
        # 時間ベースの脈動エフェクト（軽量）
        current_time = pygame.time.get_ticks()
        self.pulse_alpha = int(150 + 50 * math.sin(current_time * 0.008))  # 軽いサイン計算
        
        # 障害物との衝突判定（ボスの弾のみ、通常の弾は軽量化のためスキップ）
        if self.is_boss_bullet and USE_CSV_MAP:
            from ui.stage import get_stage_map
            stage_map = get_stage_map()
            
            # ボス弾は森(5)と石/岩(9)のみでブロック、水(7)と危険地帯(8)は通り抜ける
            tile_id = stage_map.get_tile_at_world_pos(self.x, self.y)
            if tile_id in [5, 9]:  # 森と石/岩のみでブロック
                # 障害物に当たった弾丸は削除対象にする（期限切れにする）
                self.created_time = pygame.time.get_ticks() - self.lifetime
                return

    def draw(self, screen, camera_x=0, camera_y=0):
        """弾丸の描画（キャッシュシステムで最適化）"""
        # ボスの弾は従来通りの描画（手を加えない）
        if self.is_boss_bullet:
            self._draw_boss_bullet(screen, camera_x, camera_y)
            return
            
        sx = int(self.x - camera_x)
        sy = int(self.y - camera_y)
        
        # キャッシュキーを生成（色ベース）
        cache_key = (self.base_color, self.size)
        
        # キャッシュされたサーフェスを使用
        if cache_key not in self._draw_cache:
            self._create_cached_surface(cache_key)
        
        surf = self._draw_cache[cache_key]
        r = self.size // 2
        screen.blit(surf, (sx - r, sy - r))

    def _create_cached_surface(self, cache_key):
        """描画用のサーフェスをキャッシュに作成（視認性向上エフェクト付き）"""
        color, size = cache_key
        r = size // 2
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        
        r_base, g_base, b_base = color
        
        # 視認性向上のための多層エフェクト
        # 最外層：太い白い輪郭（強調）
        pygame.draw.circle(surf, (255, 255, 255, 80), (r, r), r, 3)  # 太くして強調
        
        # 外側の発光エフェクト（大きく）
        outer_color = (min(255, r_base + 80), min(255, g_base + 80), min(255, b_base + 80), 80)
        pygame.draw.circle(surf, outer_color, (r, r), r - 1)
        
        # 中間層：元の色（濃く）
        mid_color = (r_base, g_base, b_base, 200)
        pygame.draw.circle(surf, mid_color, (r, r), r - 2)
        
        # 内側のコア（明るく）
        core_color = (min(255, r_base + 40), min(255, g_base + 40), min(255, b_base + 40))
        pygame.draw.circle(surf, core_color, (r, r), r // 2)
        
        # 中心のハイライト（明るく）
        highlight_color = (255, 255, 255, 200)
        pygame.draw.circle(surf, highlight_color, (r, r), max(2, r // 3))  # 少し大きく
        
        self._draw_cache[cache_key] = surf

    def _draw_boss_bullet(self, screen, camera_x, camera_y):
        """ボスの弾丸の描画（従来通り、変更なし）"""
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