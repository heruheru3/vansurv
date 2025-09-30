"""
ゲーム初期化処理を集約するモジュール
main.pyから初期化ロジックを分離
"""

import pygame
import sys
import multiprocessing as mp
from constants import *
import systems.resources as resources
from systems.save_system import SaveSystem
from systems.performance_logger import PerformanceLogger
from core.game_utils import init_game_state
from core.enemy_spawn_manager import EnemySpawnManager
from core.enemy import Enemy
from map import MapLoader
from ui.box import BoxManager

class GameInitializer:
    """ゲームの初期化を管理するクラス"""
    
    def __init__(self):
        self.screen = None
        self.virtual_screen = None
        self.icons = {}
        self.save_system = None
        self.performance_logger = None
        self.map_loader = None
        self.spawn_manager = None
        self.box_manager = None
        self.audio = None
        
    def initialize_pygame(self):
        """Pygameの基本初期化"""
        # マルチプロセシング対応
        mp.set_start_method('spawn', force=True)
        
        # Pygame初期化
        pygame.init()
        
        # ディスプレイ情報取得
        try:
            display_info = pygame.display.Info()
        except Exception:
            display_info = None
        
        return display_info
    
    def create_display(self):
        """ディスプレイ設定（最適化版）"""
        windowed_size = (SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # ハードウェアアクセラレーションを試みる
        try:
            if USE_HARDWARE_ACCELERATION:
                self.screen = pygame.display.set_mode(windowed_size, pygame.RESIZABLE | pygame.HWSURFACE | pygame.DOUBLEBUF)
                print("[INFO] Hardware acceleration enabled")
            else:
                self.screen = pygame.display.set_mode(windowed_size, pygame.RESIZABLE)
        except:
            # ハードウェアアクセラレーションが使えない場合は通常モード
            self.screen = pygame.display.set_mode(windowed_size, pygame.RESIZABLE)
            print("[WARNING] Hardware acceleration not available, using software rendering")
        
        pygame.display.set_caption("Van Survivor Clone")
        
        # 仮想画面（convert()で高速化）
        self.virtual_screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        if self.screen:
            self.virtual_screen = self.virtual_screen.convert(self.screen)
        
        return {
            'screen': self.screen,
            'virtual_screen': self.virtual_screen,
            'windowed_size': windowed_size,
            'is_fullscreen': False,
            'scale_factor': 1.0,
            'offset_x': 0,
            'offset_y': 0
        }
    
    def load_resources(self):
        """リソースのプリロード"""
        preload_res = resources.preload_all(icon_size=16)
        self.icons = preload_res.get('icons', {})
        return self.icons
    
    def initialize_audio(self):
        """オーディオシステムの初期化"""
        try:
            from core.audio import audio
            self.audio = audio
            audio.play_bgm('level1')
            print("[INFO] Audio system initialized")
        except Exception as e:
            print(f"[WARNING] Audio initialization failed: {e}")
            self.audio = None
    
    def preload_boss_images(self):
        """ボス画像のプリロード"""
        try:
            boss_configs = Enemy.get_all_boss_configs()
            for key, cfg in boss_configs.items():
                if isinstance(key, int):
                    try:
                        boss_no = key
                        boss_type = cfg['type']
                        Enemy._load_enemy_image(boss_type, 1, cfg.get('image_file'), boss_no=boss_no)
                    except Exception:
                        pass
            print("[INFO] Boss images preloaded")
        except Exception as e:
            print(f"[WARNING] Boss image preload failed: {e}")
    
    def initialize_save_system(self):
        """セーブシステムの初期化"""
        self.save_system = SaveSystem()
        print(f"[INFO] Save system initialized. Current money: {self.save_system.get_money()}G")
        return self.save_system
    
    def initialize_performance_logger(self):
        """パフォーマンスログシステムの初期化"""
        self.performance_logger = PerformanceLogger()
        return self.performance_logger
    
    def initialize_map(self):
        """マップローダーの初期化"""
        self.map_loader = MapLoader()
        
        if USE_CSV_MAP:
            try:
                map_path = "map/stage_map.csv"
                if self.map_loader.load_map(map_path):
                    print(f"[INFO] Map loaded from {map_path}")
                else:
                    print(f"[WARNING] Failed to load {map_path}, using default map")
                    self.map_loader.generate_default_map()
            except Exception as e:
                print(f"[ERROR] Map loading error: {e}")
                self.map_loader.generate_default_map()
        else:
            self.map_loader.generate_default_map()
        
        # ステージマップの初期化
        from ui.stage import StageMap
        self.stage_map = StageMap()
        
        return self.map_loader
    
    def initialize_spawn_manager(self):
        """エネミースポーンマネージャーの初期化"""
        try:
            self.spawn_manager = EnemySpawnManager()
            print("[INFO] Enemy spawn manager initialized")
        except Exception as e:
            print(f"[ERROR] Failed to initialize EnemySpawnManager: {e}")
            pygame.quit()
            sys.exit(1)
        
        return self.spawn_manager
    
    def initialize_game_state(self):
        """ゲーム状態の初期化"""
        game_state = init_game_state(self.screen, self.save_system)
        
        # ボックスマネージャーの初期化
        self.box_manager = BoxManager()
        
        return {
            'player': game_state[0],
            'enemies': game_state[1],
            'experience_gems': game_state[2],
            'items': game_state[3],
            'game_over': game_state[4],
            'game_clear': game_state[5],
            'spawn_timer': game_state[6],
            'spawn_interval': game_state[7],
            'game_time': game_state[8],
            'last_difficulty_increase': game_state[9],
            'particles': game_state[10],
            'damage_stats': game_state[11],
            'boss_spawn_timer': game_state[12],
            'spawned_boss_types': game_state[13],
            'box_manager': self.box_manager
        }
    
    def setup_player_callbacks(self, player, particles):
        """プレイヤーのコールバック設定"""
        def heal_effect_callback(x, y, heal_amount, is_auto=False):
            try:
                from effects.particles import HealEffect, AutoHealEffect
                if is_auto:
                    particles.append(AutoHealEffect(x, y, heal_amount))
                else:
                    particles.append(HealEffect(x, y, heal_amount))
            except Exception:
                pass
        
        player.heal_effect_callback = heal_effect_callback
    
    def initialize_camera(self, player):
        """カメラの初期設定"""
        camera_x = max(0, min(WORLD_WIDTH - SCREEN_WIDTH, player.x - SCREEN_WIDTH // 2))
        camera_y = max(0, min(WORLD_HEIGHT - SCREEN_HEIGHT, player.y - SCREEN_HEIGHT // 2))
        
        return {
            'camera_x': float(camera_x),
            'camera_y': float(camera_y),
            'CAMERA_LERP': 0.18
        }
    
    def full_initialization(self):
        """全体の初期化を実行"""
        print("[INFO] Starting full game initialization...")
        
        # 1. Pygame初期化
        display_info = self.initialize_pygame()
        
        # 2. ディスプレイ作成
        display_config = self.create_display()
        
        # 3. リソース読み込み
        self.load_resources()
        
        # 4. オーディオ初期化
        self.initialize_audio()
        
        # 5. ボス画像プリロード
        self.preload_boss_images()
        
        # 6. セーブシステム
        self.initialize_save_system()
        
        # 7. パフォーマンスログ
        self.initialize_performance_logger()
        
        # 8. マップ
        self.initialize_map()
        
        # 9. スポーンマネージャー
        self.initialize_spawn_manager()
        
        # 10. ゲーム状態
        game_state = self.initialize_game_state()
        
        # 11. プレイヤーコールバック
        self.setup_player_callbacks(game_state['player'], game_state['particles'])
        
        # 12. カメラ
        camera_config = self.initialize_camera(game_state['player'])
        
        print("[INFO] Full initialization complete!")
        
        return {
            'screen': display_config['screen'],
            'virtual_screen': display_config['virtual_screen'],
            'windowed_size': display_config['windowed_size'],
            'is_fullscreen': display_config['is_fullscreen'],
            'display_info': display_info,
            'ICONS': self.icons,
            'save_system': self.save_system,
            'performance_logger': self.performance_logger,
            'map_loader': self.map_loader,
            'spawn_manager': self.spawn_manager,
            'box_manager': self.box_manager,
            'stage_map': getattr(self, 'stage_map', None),
            'audio': self.audio,
            'game_state': game_state,
            'camera_config': camera_config
        }
