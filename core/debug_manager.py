"""
デバッグ機能を集約するモジュール
main.pyからデバッグ関連の処理を分離
"""

import pygame
import sys
from constants import *

class DebugManager:
    """デバッグ機能を管理するクラス"""
    
    def __init__(self):
        self.debug_mode = DEBUG
        self.show_status = True
        self.show_debug_visuals = False
        self.show_fps = SHOW_FPS
        self.show_pickup_range = SHOW_PICKUP_RANGE
        self.parallel_processing_enabled = PARALLEL_PROCESSING_ENABLED
        
        # フォント初期化
        try:
            self.debug_font = pygame.font.SysFont(None, 14)
            self.fps_font = pygame.font.SysFont(None, 20)
        except Exception:
            try:
                self.debug_font = pygame.font.Font(None, 14)
                self.fps_font = pygame.font.Font(None, 20)
            except Exception:
                self.debug_font = None
                self.fps_font = None
    
    def handle_debug_keys(self, event):
        """デバッグ用キー入力の処理"""
        if event.type != pygame.KEYDOWN:
            return False
        
        # F3: デバッグモード切り替え
        if event.key == pygame.K_F3:
            self.toggle_debug_mode()
            return True
        
        # F4: プレイヤーステータス表示切り替え
        if event.key == pygame.K_F4:
            self.toggle_status()
            return True
        
        # F5: デバッグ表示切り替え（攻撃範囲・敵の当たり判定）
        if event.key == pygame.K_F5:
            self.toggle_debug_visuals()
            return True
        
        # F6: FPS表示切り替え
        if event.key == pygame.K_F6:
            self.toggle_fps_display()
            return True
        
        # F7: ピックアップ範囲表示切り替え
        if event.key == pygame.K_F7:
            self.toggle_pickup_range()
            return True
        
        # F8: 並列処理切り替え
        if event.key == pygame.K_F8:
            self.toggle_parallel_processing()
            return True
        
        # F10: パフォーマンスログ切り替え
        if event.key == pygame.K_F10:
            self.toggle_performance_log()
            return True
        
        return False
    
    def toggle_debug_mode(self):
        """デバッグモードの切り替え"""
        self.debug_mode = not self.debug_mode
        
        # グローバルなDEBUG変数も更新
        global DEBUG_MODE
        DEBUG_MODE = self.debug_mode
        
        # 他モジュールのDEBUG変数を更新
        try:
            for m in list(sys.modules.values()):
                try:
                    setattr(m, 'DEBUG', self.debug_mode)
                except Exception:
                    pass
        except Exception:
            pass
        
        print(f"[INFO] DEBUG_MODE set to {self.debug_mode}")
    
    def toggle_status(self):
        """プレイヤーステータス表示の切り替え"""
        self.show_status = not self.show_status
        print(f"[INFO] show_status set to {self.show_status}")
    
    def toggle_debug_visuals(self):
        """デバッグビジュアル表示の切り替え"""
        self.show_debug_visuals = not self.show_debug_visuals
        print(f"[INFO] show_debug_visuals set to {self.show_debug_visuals}")
    
    def toggle_fps_display(self):
        """FPS表示の切り替え"""
        global SHOW_FPS
        SHOW_FPS = not SHOW_FPS
        self.show_fps = SHOW_FPS
        print(f"[INFO] SHOW_FPS set to {self.show_fps}")
    
    def toggle_pickup_range(self):
        """ピックアップ範囲表示の切り替え"""
        global SHOW_PICKUP_RANGE
        SHOW_PICKUP_RANGE = not SHOW_PICKUP_RANGE
        self.show_pickup_range = SHOW_PICKUP_RANGE
        print(f"[INFO] SHOW_PICKUP_RANGE set to {self.show_pickup_range}")
    
    def toggle_parallel_processing(self):
        """並列処理の切り替え"""
        global PARALLEL_PROCESSING_ENABLED
        PARALLEL_PROCESSING_ENABLED = not PARALLEL_PROCESSING_ENABLED
        self.parallel_processing_enabled = PARALLEL_PROCESSING_ENABLED
        print(f"[INFO] PARALLEL_PROCESSING_ENABLED set to {self.parallel_processing_enabled}")
        return self.parallel_processing_enabled
    
    def toggle_performance_log(self):
        """パフォーマンスログの切り替え"""
        global ENABLE_PERFORMANCE_LOG
        ENABLE_PERFORMANCE_LOG = not ENABLE_PERFORMANCE_LOG
        print(f"[INFO] ENABLE_PERFORMANCE_LOG set to {ENABLE_PERFORMANCE_LOG}")
    
    def draw_fps(self, screen, fps_values, enemies, experience_gems, player, gpu_assist_enabled=None):
        """FPS情報を描画（左下表示）"""
        if not self.show_fps or not self.fps_font or len(fps_values) == 0:
            return
        
        # 平均FPSを計算
        avg_fps = sum(fps_values[-30:]) / len(fps_values[-30:])
        
        # 弾丸数をカウント
        total_projectiles = sum(len(enemy.get_projectiles()) for enemy in enemies)
        
        # 回収範囲情報を取得
        pickup_range = player.get_gem_pickup_range() if hasattr(player, 'get_gem_pickup_range') else 0
        pickup_level = player.get_magnet_level() if hasattr(player, 'get_magnet_level') else 0
        
        # 統計情報を1行にまとめる（左下表示）
        gpu_status = ""
        if gpu_assist_enabled is not None:
            gpu_status = f" | GPU: {'ON' if gpu_assist_enabled else 'OFF'}"
        
        info_text = f"FPS: {avg_fps:.1f} | Enemies: {len(enemies)} | Bullets: {total_projectiles} | Gems: {len(experience_gems)} | Range: {pickup_range:.1f}px (Lv{pickup_level}){gpu_status}"
        
        text_surf = self.fps_font.render(info_text, True, (255, 255, 255))
        # 左下に配置
        text_rect = text_surf.get_rect(bottomleft=(10, screen.get_height() - 10))
        
        # 半透明背景
        bg_rect = text_rect.inflate(8, 4)
        bg_surf = pygame.Surface((bg_rect.width, bg_rect.height))
        bg_surf.set_alpha(128)
        bg_surf.fill((0, 0, 0))
        screen.blit(bg_surf, bg_rect.topleft)
        screen.blit(text_surf, text_rect)
    
    def draw_debug_info(self, screen, player, camera_x, camera_y):
        """デバッグ情報を描画"""
        if not self.debug_mode or not self.debug_font:
            return
        
        # プレイヤー座標
        pos_text = f"Pos: ({int(player.x)}, {int(player.y)})"
        cam_text = f"Cam: ({int(camera_x)}, {int(camera_y)})"
        
        y = SCREEN_HEIGHT - 50
        for line in [pos_text, cam_text]:
            text_surf = self.debug_font.render(line, True, (255, 255, 0))
            screen.blit(text_surf, (10, y))
            y += 16
    
    def should_show_debug_visuals(self):
        """デバッグビジュアルを表示すべきか"""
        return self.show_debug_visuals
    
    def should_show_status(self):
        """ステータスを表示すべきか"""
        return self.show_status
    
    def should_show_pickup_range(self):
        """ピックアップ範囲を表示すべきか"""
        return self.show_pickup_range
    
    def is_parallel_processing_enabled(self):
        """並列処理が有効か"""
        return self.parallel_processing_enabled
