import pygame
import sys
import math
import random
import os
import time
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from constants import *
from core.audio import audio

# マルチプロセシング対応関数
def process_enemy_batch(enemy_data_batch, player_data, game_data):
    """エネミーバッチの並列処理"""
    results = []
    player_x, player_y, player_half, player_avoidance = player_data
    current_time = game_data.get('current_time', 0)
    
    for enemy_data in enemy_data_batch:
        enemy_id, enemy_x, enemy_y, projectiles_data = enemy_data
        
        for proj_id, proj_x, proj_y, proj_size in projectiles_data:
            proj_half = proj_size // 2
            # 衝突判定
            if (abs(player_x - proj_x) < player_half + proj_half and 
                abs(player_y - proj_y) < player_half + proj_half):
                # 回避判定
                avoided = random.random() < player_avoidance
                results.append({
                    'enemy_id': enemy_id,
                    'projectile_id': proj_id,
                    'collision': True,
                    'avoided': avoided,
                    'hit_pos': (proj_x, proj_y)
                })
    
    return results

def process_enemy_updates(enemy_data_batch, player_data, dt):
    """エネミーの更新処理を並列化"""
    results = []
    player_x, player_y = player_data
    
    for enemy_data in enemy_data_batch:
        enemy_id, enemy_x, enemy_y, enemy_type = enemy_data
        # 簡単な移動計算（実際のAIロジックは簡素化）
        dx = player_x - enemy_x
        dy = player_y - enemy_y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance > 0:
            speed = 1.0  # 基本速度
            move_x = (dx / distance) * speed * dt
            move_y = (dy / distance) * speed * dt
            
            results.append({
                'enemy_id': enemy_id,
                'new_x': enemy_x + move_x,
                'new_y': enemy_y + move_y
            })
    
    return results

def draw_test_checkerboard(surface, camera_x, camera_y):
    """テスト用の市松模様背景を描画"""
    # 描画範囲を計算
    start_tile_x = int(camera_x // TEST_TILE_SIZE)
    end_tile_x = int((camera_x + SCREEN_WIDTH) // TEST_TILE_SIZE) + 1
    start_tile_y = int(camera_y // TEST_TILE_SIZE)
    end_tile_y = int((camera_y + SCREEN_HEIGHT) // TEST_TILE_SIZE) + 1
    
    for tile_y in range(start_tile_y, end_tile_y):
        for tile_x in range(start_tile_x, end_tile_x):
            # 市松模様の色を決定
            if (tile_x + tile_y) % 2 == 0:
                color = DARK_GRAY
            else:
                color = MOREDARK_GRAY

            # タイルの位置を計算
            screen_x = tile_x * TEST_TILE_SIZE - camera_x
            screen_y = tile_y * TEST_TILE_SIZE - camera_y
            
            # タイルを描画
            pygame.draw.rect(surface, color, 
                           (screen_x, screen_y, TEST_TILE_SIZE, TEST_TILE_SIZE))

from core.player import Player
from core.enemy import Enemy
from core.enemy_spawn_manager import EnemySpawnManager
from effects.items import ExperienceGem, GameItem, MoneyItem
from effects.particles import DeathParticle, PlayerHurtParticle, HurtFlash, LevelUpEffect, SpawnParticle, DamageNumber, AvoidanceParticle, HealEffect, AutoHealEffect
from ui.ui import draw_ui, draw_minimap, draw_level_choice, draw_end_buttons, get_end_button_rects
from ui.stage import draw_stage_background
from ui.box import BoxManager  # アイテムボックス管理用
import systems.resources as resources
from core.game_utils import init_game_state, limit_particles, enforce_experience_gems_limit
from core.game_logic import (spawn_enemies, handle_enemy_death, handle_bomb_item_effect, 
                       update_difficulty, handle_player_level_up, collect_experience_gems, collect_items)
from core.collision import check_player_enemy_collision, check_attack_enemy_collision
from map import MapLoader
from systems.save_system import SaveSystem
from systems.performance_logger import PerformanceLogger

# ランタイムで切り替え可能なデバッグフラグ（F3でトグル）
DEBUG_MODE = DEBUG

# パフォーマンス測定用のグローバル変数
performance_stats = {
    'frame_time': 0.0,
    'particle_update_time': 0.0,
    'collision_check_time': 0.0,
    'enemy_update_time': 0.0,
    'render_time': 0.0,
    'entities_count': {
        'enemies': 0,
        'particles': 0,
        'gems': 0,
        'projectiles': 0
    },
    'parallel_enabled': PARALLEL_PROCESSING_ENABLED,
    'parallel_threads': 0,
    'cpu_usage': 0.0,
    'cpu_cores_used': 0,      # 実際に使用中のCPUコア数
    'cpu_efficiency': 0.0,    # CPU効率（理論値に対する実際の使用率）
    'draw_calls': 0,          # 描画呼び出し数
    'culled_entities': 0,     # カリングされたエンティティ数
    'visible_entities': 0,    # 描画されたエンティティ数
}

def measure_time(func):
    """時間測定デコレータ"""
    def wrapper(*args, **kwargs):
        start_time = pygame.time.get_ticks()
        result = func(*args, **kwargs)
        end_time = pygame.time.get_ticks()
        return result, (end_time - start_time)
    return wrapper

def draw_performance_stats(surface, font):
    """パフォーマンス統計を描画"""
    if not SHOW_PERFORMANCE_STATS or not font:
        return
    
    stats = performance_stats
    y_offset = 200  # FPS表示の下に配置
    
    # パフォーマンス統計のテキスト作成
    perf_texts = [
        f"=== Performance Stats ===",
        f"Frame: {stats['frame_time']:.1f}ms",
        f"Particles: {stats['particle_update_time']:.1f}ms",
        f"Collision: {stats['collision_check_time']:.1f}ms", 
        f"Enemies: {stats['enemy_update_time']:.1f}ms",
        f"Render: {stats['render_time']:.1f}ms",
        f"",
        f"=== CPU Usage ===",
        f"CPU: {stats.get('cpu_usage', 0):.1f}% ({stats.get('cpu_cores_used', 0)}/{mp.cpu_count()} cores)",
        f"CPU Efficiency: {stats.get('cpu_efficiency', 0):.1f}%",
        f"Threads: {stats.get('parallel_threads', 0)}",
        f"",
        f"=== Entity Counts ===",
        f"Enemies: {stats['entities_count']['enemies']}",
        f"Particles: {stats['entities_count']['particles']}",
        f"Gems: {stats['entities_count']['gems']}",
        f"Projectiles: {stats['entities_count']['projectiles']}",
        f"",
        f"Parallel: {'ON' if stats['parallel_enabled'] else 'OFF'}",
        f"F8: Toggle Parallel Processing",
        f"F9: Toggle Performance Stats",
        f"F10: Toggle Performance Log"
    ]
    
    for i, text in enumerate(perf_texts):
        if text:  # 空行はスキップ
            color = GREEN if "ON" in text else (RED if "OFF" in text else WHITE)
            text_surface = font.render(text, True, color)
            surface.blit(text_surface, (10, y_offset + i * 15))


def main():
    global DEBUG_MODE
    
    # マルチプロセシング対応の初期化
    mp.set_start_method('spawn', force=True)  # Windowsでの安定性向上
    
    # 初期化
    pygame.init()
    
    # ステージを最初に初期化（プレイヤーの安全な開始位置決定のため、マップが有効な場合のみ）
   
    # ディスプレイ情報取得（フルスクリーン切替に使用）
    try:
        display_info = pygame.display.Info()
    except Exception:
        display_info = None

    # ウィンドウサイズ（通常モード）
    windowed_size = (SCREEN_WIDTH, SCREEN_HEIGHT)
    current_size = windowed_size
    # フルスクリーンフラグ（ウィンドウフルスクリーンタイプのトグルに使用）
    is_fullscreen = False

    # 初期はリサイズ可能なウィンドウモードで開始
    screen = pygame.display.set_mode(windowed_size, pygame.RESIZABLE)
    pygame.display.set_caption("Van Survivor Clone")
    
    # 仮想画面（ゲームロジックは常にこのサイズで動作）
    virtual_screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    
    # スケーリング係数（描画用）とキャッシュサーフェス
    scale_factor = 1.0
    offset_x = 0
    offset_y = 0
    scaled_surface = None  # スケール済みサーフェスのキャッシュ

    # リソースをプリロード（アイコン・フォント・サウンド等）
    preload_res = resources.preload_all(icon_size=16)
    ICONS = preload_res.get('icons', {})

    # Start background music (level1) if available
    try:
        # from audio import audio (先頭でインポート済み)
        audio.play_bgm('level1')
    except Exception:
        pass

    # デバッグ: 起動時にオーディオ初期化と簡易再生テストを行う（問題切り分け用）
    try:
        pass
    except Exception:
        pass

    # --- ボス設定のプリロード: ボス画像を事前に読み込んでおく（スポーン時のIO/変換を避ける）
    try:
        from core.enemy import Enemy
        # get_all_boss_configs 内で load_boss_stats が呼ばれる
        boss_configs = Enemy.get_all_boss_configs()
        # 画像を一通りキャッシュしておく（Noベースのエントリのみ）
        for key, cfg in boss_configs.items():
            if isinstance(key, int):  # Noベースのエントリのみ処理
                try:
                    boss_no = key
                    boss_type = cfg['type']
                    Enemy._load_enemy_image(boss_type, 1, cfg.get('image_file'), boss_no=boss_no)
                except Exception:
                    pass
    except Exception:
        pass

    # セーブシステムを初期化
    save_system = SaveSystem()
    print(f"[INFO] Save system initialized. Current money: {save_system.get_money()}G")

    # パフォーマンスログシステムを初期化
    performance_logger = PerformanceLogger()
    log_timer = 0.0  # ログ出力タイマー

    clock = pygame.time.Clock()
    # FPSカウンター用
    fps_values = []
    fps_update_timer = 0.0
    
    # 画面右下に小さなプレイヤーステータスを表示するかどうかのフラグ（F4でトグル）
    show_status = True
    # デバッグ表示フラグ（F5でトグル：攻撃範囲＋敵の当たり判定）
    show_debug_visuals = False
    try:
        debug_font = pygame.font.SysFont(None, 14)
        fps_font = pygame.font.SysFont(None, 20)  # FPS表示用フォント
    except Exception:
        try:
            # システムフォントが使えない場合はデフォルトフォントを使用
            debug_font = pygame.font.Font(None, 14)
            fps_font = pygame.font.Font(None, 20)
        except Exception:
            debug_font = None
            fps_font = None

    # カメラ初期値とスムージング係数（0.0: 固定、1.0: 即時追従）
    camera_x = 0.0
    camera_y = 0.0
    CAMERA_LERP = 0.18

    # ゲーム状態の初期化
    player, enemies, experience_gems, items, game_over, game_clear, spawn_timer, spawn_interval, game_time, last_difficulty_increase, particles, damage_stats, boss_spawn_timer, spawned_boss_types = init_game_state(screen, save_system)

    # エネミースポーンマネージャーの初期化
    try:
        spawn_manager = EnemySpawnManager()
    except Exception as e:
        print(f"ERROR: Failed to initialize EnemySpawnManager: {e}")
        pygame.quit()
        sys.exit(1)
    
    # エンド画面のキーボード選択状態
    end_screen_selection = 0  # 0: Restart (left), 1: Continue (right)

    # ステージマップのインスタンスを作成
    from ui.stage import StageMap
    stage_map = StageMap()

    # マルチプロセシング対応の並列処理関数
    def aggressive_parallel_update_enemies(enemies, player_data, dt, camera_data, map_loader):
        """エネミー更新の積極的並列処理（ProcessPoolExecutor使用でCPU使用率最大化）"""
        if not PARALLEL_PROCESSING_ENABLED or len(enemies) <= 1:
            return enemies  # 逐次処理にフォールバック
        
        try:
            # CPUコア数フル活用
            num_processes = min(mp.cpu_count(), 8)
            performance_stats['parallel_threads'] = max(performance_stats.get('parallel_threads', 0), num_processes)
            
            # エネミーを小さなバッチに分割（より多くのプロセスを活用）
            batch_size = max(1, len(enemies) // (num_processes * 2))  # プロセス数の2倍のバッチ数
            enemy_batches = [enemies[i:i + batch_size] for i in range(0, len(enemies), batch_size)]
            
            # 複数の処理を並列実行
            with ProcessPoolExecutor(max_workers=num_processes) as executor:
                def process_enemy_batch_intensive(batch, dt):
                    """CPU集約的なエネミー処理"""
                    for enemy in batch:
                        try:
                            # 移動計算（CPU集約的）
                            dx = player_data['x'] - enemy.x
                            dy = player_data['y'] - enemy.y
                            distance = (dx * dx + dy * dy) ** 0.5
                            
                            # AI行動計算（CPU集約的）
                            if hasattr(enemy, 'update_ai_behavior'):
                                enemy.update_ai_behavior(distance, dx, dy)
                            
                            # ノックバック処理
                            if hasattr(enemy, 'update_knockback'):
                                enemy.update_knockback(dt * (1.0/60.0))
                        except Exception:
                            pass
                    return batch
                
                # 並列実行でCPU使用率を最大化（delta_timeを渡す）
                futures = [executor.submit(process_enemy_batch_intensive, batch, delta_time) for batch in enemy_batches]
                results = [future.result() for future in futures]
                
                # 結果をマージ
                updated_enemies = []
                for batch_result in results:
                    updated_enemies.extend(batch_result)
                return updated_enemies
                
        except Exception:
            return enemies  # エラー時は元のリストを返す

    def parallel_update_particles(particles):
        """パーティクルの並列更新処理"""
        # 並列処理が無効化されている場合は逐次処理
        if not PARALLEL_PROCESSING_ENABLED:
            new_particles = []
            for p in particles:
                try:
                    if p.update():
                        new_particles.append(p)
                except Exception:
                    pass
            return new_particles
            
        max_particles = PARTICLE_LIMIT
        if len(particles) > max_particles:
            particles = particles[-max_particles:]
        
        if len(particles) <= 5:  # 閾値を10から5に大幅に下げる（並列処理をより積極的に使用）
            # 少数の場合は逐次処理が高速
            new_particles = []
            for p in particles:
                try:
                    if p.update():
                        new_particles.append(p)
                except Exception:
                    pass
            return new_particles
        
        # 大量の場合はマルチスレッド処理
        try:
            num_threads = min(mp.cpu_count(), 8)  # 8コア環境をフル活用（6→8に増加）
            performance_stats['parallel_threads'] = max(performance_stats.get('parallel_threads', 0), num_threads)
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                # パーティクルを複数のバッチに分割
                batch_size = max(1, len(particles) // num_threads)
                batches = [particles[i:i + batch_size] for i in range(0, len(particles), batch_size)]
                
                def update_batch(batch):
                    result = []
                    for p in batch:
                        try:
                            if p.update():
                                result.append(p)
                        except Exception:
                            pass
                    return result
                
                futures = [executor.submit(update_batch, batch) for batch in batches]
                
                # 結果をまとめる
                new_particles = []
                for future in futures:
                    new_particles.extend(future.result())
                return new_particles
                
        except Exception:
            # エラー時は逐次処理にフォールバック
            new_particles = []
            for p in particles:
                try:
                    if p.update():
                        new_particles.append(p)
                except Exception:
                    pass
            return new_particles

    def parallel_collision_check(enemies, player, total_projectiles):
        """衝突判定の並列処理"""
        # 並列処理が無効化されている場合は逐次処理
        if not PARALLEL_PROCESSING_ENABLED:
            return sequential_collision_check(enemies, player, total_projectiles)
            
        if len(enemies) <= 2 or total_projectiles <= 5:  # 閾値を大幅に下げる（5→2, 20→5）より積極的な並列化
            # 少数の場合は逐次処理
            return sequential_collision_check(enemies, player, total_projectiles)
        
        try:
            # エネミーデータを準備
            enemy_data = []
            for i, enemy in enumerate(enemies):
                projectiles = enemy.get_projectiles()
                projectiles_data = [(j, p.x, p.y, p.size) for j, p in enumerate(projectiles)]
                enemy_data.append((i, enemy.x, enemy.y, projectiles_data))
            
            # プレイヤーデータ
            player_data = (player.x, player.y, getattr(player, 'size', 32) // 2, player.get_avoidance())
            game_data = {'current_time': pygame.time.get_ticks()}
            
            # バッチに分割（CPUコア数に基づく）
            num_cores = min(mp.cpu_count(), 8)  # 8コア環境をフル活用（6→8に増加）
            performance_stats['parallel_threads'] = max(performance_stats.get('parallel_threads', 0), num_cores)
            batch_size = max(1, len(enemy_data) // num_cores)
            batches = [enemy_data[i:i + batch_size] for i in range(0, len(enemy_data), batch_size)]
            
            collision_results = []
            with ThreadPoolExecutor(max_workers=num_cores) as executor:
                futures = [executor.submit(process_enemy_batch, batch, player_data, game_data) for batch in batches]
                for future in futures:
                    collision_results.extend(future.result())
            
            return collision_results
            
        except Exception as e:
            # エラー時は逐次処理にフォールバック
            return sequential_collision_check(enemies, player, total_projectiles)

    def sequential_collision_check(enemies, player, total_projectiles):
        """従来の逐次衝突判定（フォールバック用）"""
        collision_results = []
        player_half = getattr(player, 'size', 32) // 2
        
        for i, enemy in enumerate(enemies):
            projectiles = enemy.get_projectiles()
            for j, projectile in enumerate(projectiles):
                proj_half = projectile.size // 2
                if (abs(player.x - projectile.x) < player_half + proj_half and 
                    abs(player.y - projectile.y) < player_half + proj_half):
                    avoided = random.random() < player.get_avoidance()
                    collision_results.append({
                        'enemy_id': i,
                        'projectile_id': j,
                        'collision': True,
                        'avoided': avoided,
                        'hit_pos': (projectile.x, projectile.y)
                    })
        return collision_results

    # お金関連の初期化
    current_game_money = 0  # 現在のゲームセッションで獲得したお金
    enemies_killed_this_game = 0  # 今回のゲームで倒した敵の数
    enemy_kill_stats = {}  # エネミーNo.別撃破数統計
    boss_kill_stats = {}  # ボスNo.別撃破数統計
    force_ended = False  # ESCキーによる強制終了フラグ
    
    # ボックスマネージャーの初期化
    box_manager = BoxManager()

    # マップローダーの初期化
    map_loader = MapLoader()
    if USE_CSV_MAP:
        # CSVマップファイルを読み込み（存在しない場合はサンプルを作成）
        csv_path = CSV_MAP_FILE
        
        # 通常のPython実行時のみサンプル作成
        try:
            # PyInstallerで実行されているか確認
            import sys
            is_frozen = getattr(sys, 'frozen', False)
        except:
            is_frozen = False
            
        if not is_frozen and not os.path.exists(csv_path):
            map_loader.create_sample_csv(csv_path)
            
        # マップを読み込み（PyInstallerの場合はリソースから）
        success = map_loader.load_csv_map(csv_path)
        if not success:
            map_loader.generate_default_map()
    else:
        # デフォルトマップ（市松模様）を生成
        map_loader.generate_default_map()

    # カメラをプレイヤーの初期位置に設定
    camera_x = max(0, min(WORLD_WIDTH - SCREEN_WIDTH, player.x - SCREEN_WIDTH // 2))
    camera_y = max(0, min(WORLD_HEIGHT - SCREEN_HEIGHT, player.y - SCREEN_HEIGHT // 2))

    # HP回復エフェクト用のコールバックを設定
    def heal_effect_callback(x, y, heal_amount, is_auto=False):
        if is_auto:
            particles.append(AutoHealEffect(x, y))
        particles.append(HealEffect(x, y, heal_amount))
        # サウンド再生（回復）
        try:
            # from audio import audio (先頭でインポート済み)
            audio.play_sound('heal', duration=0.5, fade_out=0.1)
        except Exception:
            pass
    
    player.heal_effect_callback = heal_effect_callback

    # メインゲームループ
    running = True
    frame_count = 0  # フレームカウンターを初期化
    
    # デルタタイム管理の初期化
    last_time = time.perf_counter() * 1000.0  # ミリ秒に変換
    accumulator = 0.0  # フレーム更新の蓄積時間
    game_time_accumulator = 0.0  # ゲーム時間の蓄積
    
    print("[INFO] Entering main loop with delta time system")
    while running:
        try:
            # デルタタイム計算（エクスポネンシャル・スムージング）
            current_time = time.perf_counter() * 1000.0  # ミリ秒に変換
            delta_time_ms = current_time - last_time
            last_time = current_time
            
            # エクスポネンシャル・スムージングの初期化
            if not hasattr(main, 'smoothed_delta_time_ms'):
                main.smoothed_delta_time_ms = delta_time_ms
            
            # エクスポネンシャル・スムージング（より滑らかな補間）
            main.smoothed_delta_time_ms = (
                DELTA_TIME_SMOOTHING * delta_time_ms + 
                (1.0 - DELTA_TIME_SMOOTHING) * main.smoothed_delta_time_ms
            )
            
            # デルタタイムのキャップ（異常な値を防ぐ）
            if main.smoothed_delta_time_ms > DELTA_TIME_CAP:
                main.smoothed_delta_time_ms = DELTA_TIME_CAP
            
            # デルタタイムを60FPS基準で正規化（1.0 = 60FPSでの1フレーム）
            delta_time = main.smoothed_delta_time_ms / TARGET_FRAME_TIME
            
            # デバッグ：delta_time値を定期的に表示（10フレームごと）
            # フレームスキップ判定
            frame_skip_count = 0
            if ENABLE_FRAME_SKIP and main.smoothed_delta_time_ms > TARGET_FRAME_TIME:
                # FPSが低下している場合のフレームスキップ計算
                frame_skip_count = min(int(main.smoothed_delta_time_ms / TARGET_FRAME_TIME) - 1, MAX_FRAME_SKIP)
            
            # ゲーム更新の蓄積時間に追加
            accumulator += delta_time
            
            # フレーム開始時間を記録（高精度）
            frame_start_time = time.perf_counter()
            
            # 並列処理スレッド数をリセット（フレーム開始時）
            performance_stats['parallel_threads'] = 0
            
            # エンティティ数を記録
            total_projectiles = sum(len(enemy.get_projectiles()) for enemy in enemies)
            performance_stats['entities_count'].update({
                'enemies': len(enemies),
                'particles': len(particles),
                'gems': len(experience_gems),
                'projectiles': total_projectiles
            })
            
            # CPU効率測定（8コア環境での実際の使用率）
            try:
                actual_threads = performance_stats.get('parallel_threads', 0)
                max_threads = mp.cpu_count()
                if max_threads > 0:
                    performance_stats['cpu_cores_used'] = actual_threads
                    performance_stats['cpu_efficiency'] = (actual_threads / max_threads) * 100.0
                else:
                    performance_stats['cpu_cores_used'] = 0
                    performance_stats['cpu_efficiency'] = 0.0
            except Exception:
                performance_stats['cpu_cores_used'] = 0
                performance_stats['cpu_efficiency'] = 0.0
            # イベント処理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    # ウィンドウリサイズ処理（アスペクト比16:9を維持）
                    new_width, new_height = event.w, event.h
                    
                    # 最小サイズを元のサイズの半分に制限
                    min_width = SCREEN_WIDTH // 2
                    min_height = SCREEN_HEIGHT // 2
                    new_width = max(new_width, min_width)
                    new_height = max(new_height, min_height)
                    
                    # アスペクト比を維持するためのスケール計算
                    target_aspect = SCREEN_WIDTH / SCREEN_HEIGHT  # 16:9 = 1.777...
                    current_aspect = new_width / new_height
                    
                    if current_aspect > target_aspect:
                        # ウィンドウが横に広すぎる場合、高さを基準にする
                        scale_factor = new_height / SCREEN_HEIGHT
                        scaled_width = int(SCREEN_WIDTH * scale_factor)
                        scaled_height = new_height
                        offset_x = (new_width - scaled_width) // 2
                        offset_y = 0
                    else:
                        # ウィンドウが縦に長すぎる場合、幅を基準にする
                        scale_factor = new_width / SCREEN_WIDTH
                        scaled_width = new_width
                        scaled_height = int(SCREEN_HEIGHT * scale_factor)
                        offset_x = 0
                        offset_y = (new_height - scaled_height) // 2
                    
                    # スケール済みサーフェスのキャッシュをクリア
                    scaled_surface = None
                    
                    current_size = (new_width, new_height)
                    screen = pygame.display.set_mode(current_size, pygame.RESIZABLE)
                    
                elif event.type == pygame.KEYDOWN:
                    # デバッグログのオン/オフ切り替え（F3）
                    if event.key == pygame.K_F3:
                        DEBUG_MODE = not DEBUG_MODE
                        # 他モジュールで直接 DEBUG を参照している箇所があるため、読み込まれているモジュール内の DEBUG 変数を一括更新する
                        try:
                            for m in list(sys.modules.values()):
                                try:
                                    setattr(m, 'DEBUG', DEBUG_MODE)
                                except Exception:
                                    pass
                        except Exception:
                            pass
                        print(f"[INFO] DEBUG_MODE set to {DEBUG_MODE}")
                        continue

                    # プレイヤーステータス表示のオン/オフ切り替え（F4）
                    if event.key == pygame.K_F4:
                        show_status = not show_status
                        print(f"[INFO] show_status set to {show_status}")
                        continue

                    # デバッグ表示のトグル（F5：攻撃範囲＋敵の当たり判定）
                    if event.key == pygame.K_F5:
                        show_debug_visuals = not show_debug_visuals
                        print(f"[INFO] show_debug_visuals set to {show_debug_visuals}")
                        continue

                    # FPS表示のトグル（F6）
                    if event.key == pygame.K_F6:
                        global SHOW_FPS
                        SHOW_FPS = not SHOW_FPS
                        print(f"[INFO] SHOW_FPS set to {SHOW_FPS}")
                        continue

                    if event.key == pygame.K_F7:
                        global SHOW_PICKUP_RANGE
                        SHOW_PICKUP_RANGE = not SHOW_PICKUP_RANGE
                        print(f"[INFO] SHOW_PICKUP_RANGE set to {SHOW_PICKUP_RANGE}")
                        continue

                    # 並列処理のオン/オフ切り替え（F8）
                    if event.key == pygame.K_F8:
                        global PARALLEL_PROCESSING_ENABLED
                        PARALLEL_PROCESSING_ENABLED = not PARALLEL_PROCESSING_ENABLED
                        performance_stats['parallel_enabled'] = PARALLEL_PROCESSING_ENABLED
                        print(f"[INFO] PARALLEL_PROCESSING_ENABLED set to {PARALLEL_PROCESSING_ENABLED}")
                        continue

                    # パフォーマンス統計表示のオン/オフ切り替え（F9）
                    if event.key == pygame.K_F9:
                        global SHOW_PERFORMANCE_STATS
                        SHOW_PERFORMANCE_STATS = not SHOW_PERFORMANCE_STATS
                        print(f"[INFO] SHOW_PERFORMANCE_STATS set to {SHOW_PERFORMANCE_STATS}")
                        continue

                    # パフォーマンスログのオン/オフ切り替え（F10）
                    if event.key == pygame.K_F10:
                        enabled = performance_logger.toggle_logging()
                        print(f"[INFO] Performance logging {'enabled' if enabled else 'disabled'}")
                        if enabled:
                            print(f"[INFO] Log file: {performance_logger.log_file}")
                        continue

                    # ESCキーでゲーム途中でも強制終了
                    if event.key == pygame.K_ESCAPE and not game_over and not game_clear:
                        print("[INFO] Game forcibly ended by ESC key")
                        # 強制終了フラグを立てる（game_overと同じ扱い）
                        game_over = True
                        force_ended = True  # 強制終了フラグ
                        # セーブデータに記録
                        save_system.add_money(current_game_money + int(game_time * MONEY_PER_SURVIVAL_SECOND))
                        save_system.record_game_end(game_time, player.level, enemies_killed_this_game, player.exp)
                        # 武器使用統計も記録
                        if damage_stats:
                            save_system.record_weapon_usage(damage_stats)
                        # 実績チェック
                        save_system.check_achievements()
                        save_system.save()
                        print(f"[INFO] Game data saved (forced end). Total money now: {save_system.get_money()}G")
                        continue

                    # フルスクリーン切替（F11）
                    if event.key == pygame.K_F11:
                        try:
                            is_fullscreen = not is_fullscreen
                            if is_fullscreen:
                                # フルスクリーンモードに切り替え
                                screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                                current_size = screen.get_size()
                                print(f"[INFO] Switched to fullscreen: {current_size}")
                            else:
                                # ウィンドウモードに戻す
                                screen = pygame.display.set_mode(windowed_size, pygame.RESIZABLE)
                                current_size = windowed_size
                                print(f"[INFO] Switched to windowed: {current_size}")
                            
                            # スケーリング パラメータを再計算
                            new_width, new_height = current_size
                            aspect_ratio = SCREEN_WIDTH / SCREEN_HEIGHT
                            screen_aspect_ratio = new_width / new_height
                            
                            if screen_aspect_ratio > aspect_ratio:
                                # 画面の方が横長：高さベースでスケール
                                scale_factor = new_height / SCREEN_HEIGHT
                                scaled_width = int(SCREEN_WIDTH * scale_factor)
                                scaled_height = new_height
                                offset_x = (new_width - scaled_width) // 2
                                offset_y = 0
                            else:
                                # 画面の方が縦長：幅ベースでスケール
                                scale_factor = new_width / SCREEN_WIDTH
                                scaled_width = new_width
                                scaled_height = int(SCREEN_HEIGHT * scale_factor)
                                offset_x = 0
                                offset_y = (new_height - scaled_height) // 2
                            
                            # スケール済みサーフェスのキャッシュをクリア
                            scaled_surface = None
                            
                        except Exception as e:
                            print(f"[ERROR] Failed to toggle fullscreen: {e}")
                        continue

                    # 武器/サブアイテム選択のキー処理
                    try:
                        if getattr(player, 'awaiting_weapon_choice', False) and getattr(player, 'last_level_choices', None):
                            n = len(player.last_level_choices)
                            if n > 0:
                                # 初期武器選択（グリッド形式）の場合
                                if getattr(player, 'is_initial_weapon_selection', False):
                                    grid_size = 3
                                    current_index = getattr(player, 'selected_weapon_choice_index', 0)
                                    current_row = current_index // grid_size
                                    current_col = current_index % grid_size
                                    
                                    new_index = current_index
                                    
                                    if event.key in (pygame.K_LEFT, pygame.K_a):
                                        new_col = (current_col - 1) % grid_size
                                        new_index = current_row * grid_size + new_col
                                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                                        new_col = (current_col + 1) % grid_size
                                        new_index = current_row * grid_size + new_col
                                    elif event.key in (pygame.K_UP, pygame.K_w):
                                        new_row = (current_row - 1) % grid_size
                                        new_index = new_row * grid_size + current_col
                                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                                        new_row = (current_row + 1) % grid_size
                                        new_index = new_row * grid_size + current_col
                                    elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5,
                                                       pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9):
                                        # 数字キーで直接選択
                                        digit = event.key - pygame.K_1  # 0-8
                                        if digit < n:
                                            new_index = digit
                                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                                        # 選択確定
                                        player.set_input_method("keyboard")
                                        idx = max(0, min(current_index, n - 1))
                                        choice = player.last_level_choices[idx]
                                        player.apply_level_choice(choice)
                                        player.is_initial_weapon_selection = False
                                        try:
                                            for _ in range(8):
                                                particles.append(DeathParticle(player.x, player.y, CYAN))
                                        except Exception:
                                            pass
                                        continue
                                    
                                    # インデックス更新
                                    if new_index != current_index and new_index < n:
                                        player.set_input_method("keyboard")
                                        player.selected_weapon_choice_index = new_index
                                        try:
                                            particles.append(DeathParticle(player.x, player.y, CYAN))
                                        except Exception:
                                            pass
                                    continue
                                else:
                                    # 通常のレベルアップ選択（横並び3択）
                                    if event.key in (pygame.K_LEFT, pygame.K_a):
                                        player.set_input_method("keyboard")
                                        player.selected_weapon_choice_index = (player.selected_weapon_choice_index - 1) % n
                                        try:
                                            particles.append(DeathParticle(player.x, player.y, CYAN))
                                        except Exception:
                                            pass
                                        continue
                                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                                        player.set_input_method("keyboard")
                                        player.selected_weapon_choice_index = (player.selected_weapon_choice_index + 1) % n
                                        try:
                                            particles.append(DeathParticle(player.x, player.y, CYAN))
                                        except Exception:
                                            pass
                                        continue
                                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                                        player.set_input_method("keyboard")
                                        idx = max(0, min(player.selected_weapon_choice_index, n - 1))
                                        choice = player.last_level_choices[idx]
                                        player.apply_level_choice(choice)
                                        try:
                                            for _ in range(8):
                                                particles.append(DeathParticle(player.x, player.y, CYAN))
                                        except Exception:
                                            pass
                                        continue
                        elif getattr(player, 'awaiting_subitem_choice', False) and getattr(player, 'last_subitem_choices', None):
                            n = len(player.last_subitem_choices)
                            if n > 0:
                                if event.key in (pygame.K_LEFT, pygame.K_a):
                                    player.set_input_method("keyboard")
                                    player.selected_subitem_choice_index = (player.selected_subitem_choice_index - 1) % n
                                    try:
                                        particles.append(DeathParticle(player.x, player.y, CYAN))
                                    except Exception:
                                        pass
                                    continue
                                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                                    player.set_input_method("keyboard")
                                    player.selected_subitem_choice_index = (player.selected_subitem_choice_index + 1) % n
                                    try:
                                        particles.append(DeathParticle(player.x, player.y, CYAN))
                                    except Exception:
                                        pass
                                    continue
                                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                                    player.set_input_method("keyboard")
                                    idx = max(0, min(player.selected_subitem_choice_index, n - 1))
                                    key = player.last_subitem_choices[idx]
                                    player.apply_subitem_choice(key)
                                    try:
                                        for _ in range(8):
                                            particles.append(DeathParticle(player.x, player.y, CYAN))
                                    except Exception:
                                        pass
                                    continue
                    except Exception:
                        pass

                    # エンド画面でのキーボード操作
                    if game_over or game_clear:
                        if event.key in (pygame.K_LEFT, pygame.K_a):
                            if not game_clear:  # GameClear時は選択変更無効
                                end_screen_selection = max(0, end_screen_selection - 1)
                        elif event.key in (pygame.K_RIGHT, pygame.K_d):
                            if not game_clear:  # GameClear時は選択変更無効
                                end_screen_selection = min(1, end_screen_selection + 1)
                        elif event.key == pygame.K_RETURN:
                            # 選択されたボタンを実行
                            if end_screen_selection == 1 and game_over:  # Continue (right) - GameOverのみ
                                player.hp = player.get_max_hp()
                                player.set_special_invincible(3.0)
                                game_over = False
                                force_ended = False  # 強制終了フラグもリセット
                                for _ in range(8):
                                    particles.append(DeathParticle(player.x, player.y, CYAN))
                            elif end_screen_selection == 0 or game_clear:  # Restart (left) または GameClear時
                                # ゲームクリア時のボーナス処理
                                if game_clear:
                                    print("[INFO] Survived required time - continuing without resetting player/weapons.")
                                    current_game_money += MONEY_GAME_CLEAR_BONUS
                                    save_system.add_money(current_game_money + int(game_time * MONEY_PER_SURVIVAL_SECOND))
                                    save_system.record_game_end(game_time, player.level, enemies_killed_this_game, player.exp)
                                    if damage_stats:
                                        save_system.record_weapon_usage(damage_stats)
                                    save_system.check_achievements()
                                    save_system.save()
                                    print(f"[INFO] Game data saved. Total money now: {save_system.get_money()}G")
                                else:
                                    # ゲームオーバー時のリスタート処理
                                    save_system.add_money(current_game_money + int(game_time * MONEY_PER_SURVIVAL_SECOND))
                                    save_system.record_game_end(game_time, player.level, enemies_killed_this_game, player.exp)
                                    if damage_stats:
                                        save_system.record_weapon_usage(damage_stats)
                                    save_system.check_achievements()
                                    save_system.save()
                                    print(f"[INFO] Game data saved. Total money now: {save_system.get_money()}G")
                                
                                # 共通のリセット処理
                                enemies = []
                                experience_gems = []
                                items = []
                                particles = []
                                spawn_timer = 0
                                boss_spawn_timer = 0
                                spawn_interval = 60
                                game_time = 0
                                last_difficulty_increase = 0
                                game_clear = False
                                game_over = False
                                current_game_money = 0
                                enemies_killed_this_game = 0
                                enemy_kill_stats = {}
                                boss_kill_stats = {}
                                force_ended = False  # 強制終了フラグもリセット
                                box_manager = BoxManager()
                            
                            # 選択状態をリセット
                            end_screen_selection = 0
                            continue

                    # HP回復エフェクト用のコールバックを設定
                    def heal_effect_callback(x, y, heal_amount, is_auto=False):
                        if is_auto:
                            particles.append(AutoHealEffect(x, y))
                        particles.append(HealEffect(x, y, heal_amount))
                    player.heal_effect_callback = heal_effect_callback
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # マウスで選択可能ならクリック位置を判定
                    if getattr(player, 'awaiting_weapon_choice', False) and event.button == 1:
                        player.set_input_method("mouse")
                        # マウス座標を仮想画面座標に変換
                        mouse_x, mouse_y = event.pos
                        virtual_x = (mouse_x - offset_x) / scale_factor if scale_factor > 0 else mouse_x
                        virtual_y = (mouse_y - offset_y) / scale_factor if scale_factor > 0 else mouse_y
                        virtual_x = max(0, min(SCREEN_WIDTH, virtual_x))
                        virtual_y = max(0, min(SCREEN_HEIGHT, virtual_y))
                        mx, my = int(virtual_x), int(virtual_y)
                        
                        choices = getattr(player, 'last_level_choices', [])
                        if choices:
                            # 初期武器選択（グリッド形式）の場合
                            if getattr(player, 'is_initial_weapon_selection', False):
                                # グリッドパネルの当たり判定（レベルアップと同じレイアウト）
                                grid_size = 3
                                cw = min(880, SCREEN_WIDTH - 160)
                                option_w = (cw - 40) // grid_size
                                option_h = 142
                                cell_margin = 8
                                panel_w = cw
                                panel_h = grid_size * (option_h + cell_margin) + 100
                                
                                cx = SCREEN_WIDTH // 2
                                cy = SCREEN_HEIGHT // 2
                                # パネルが画面からはみ出ないように調整
                                panel_y = max(20, cy - panel_h // 2)
                                if panel_y + panel_h > SCREEN_HEIGHT - 20:
                                    panel_y = SCREEN_HEIGHT - panel_h - 20
                                panel_rect = pygame.Rect(cx - panel_w // 2, panel_y, panel_w, panel_h)
                                accent_h = 54
                                
                                for i, weapon_key in enumerate(choices[:9]):
                                    row = i // grid_size
                                    col = i % grid_size
                                    
                                    rect_x = panel_rect.x + 20 + col * option_w
                                    rect_y = panel_rect.y + accent_h + 12 + row * (option_h + cell_margin)
                                    rect = pygame.Rect(rect_x, rect_y, option_w - 8, option_h)
                                    
                                    if rect.collidepoint(mx, my):
                                        choice = choices[i]
                                        player.apply_level_choice(choice)
                                        player.is_initial_weapon_selection = False
                                        try:
                                            for _ in range(8):
                                                particles.append(DeathParticle(player.x, player.y, CYAN))
                                        except Exception:
                                            pass
                                        break
                            else:
                                # 通常のレベルアップ選択（横並び3択）
                                cw = min(880, SCREEN_WIDTH - 160)
                                ch = 180
                                cx = SCREEN_WIDTH // 2
                                cy = SCREEN_HEIGHT // 2
                                panel_rect = pygame.Rect(cx - cw//2, cy - ch//2, cw, ch)
                                option_w = (cw - 40) // len(choices)
                                option_h = ch - 60
                                hit = False
                                for i, choice in enumerate(choices):
                                    ox = panel_rect.x + 20 + i * option_w
                                    oy = panel_rect.y + 40
                                    rect = pygame.Rect(ox, oy, option_w - 8, option_h)
                                    if rect.collidepoint(mx, my):
                                        player.apply_level_choice(choice)
                                        try:
                                            for _ in range(8):
                                                particles.append(DeathParticle(player.x, player.y, CYAN))
                                        except Exception:
                                            pass
                                        hit = True
                                        break
                                if hit:
                                    continue
                    # サブアイテム選択のマウスクリック判定
                    if getattr(player, 'awaiting_subitem_choice', False) and event.button == 1:
                        player.set_input_method("mouse")
                        # マウス座標を仮想画面座標に変換
                        mouse_x, mouse_y = event.pos
                        virtual_x = (mouse_x - offset_x) / scale_factor if scale_factor > 0 else mouse_x
                        virtual_y = (mouse_y - offset_y) / scale_factor if scale_factor > 0 else mouse_y
                        virtual_x = max(0, min(SCREEN_WIDTH, virtual_x))
                        virtual_y = max(0, min(SCREEN_HEIGHT, virtual_y))
                        mx, my = int(virtual_x), int(virtual_y)
                        choices = getattr(player, 'last_subitem_choices', [])
                        if choices:
                            cw = min(700, SCREEN_WIDTH - 200)
                            ch = 180
                            cx = SCREEN_WIDTH // 2
                            cy = SCREEN_HEIGHT // 2
                            panel_rect = pygame.Rect(cx - cw//2, cy - ch//2, cw, ch)
                            option_w = (cw - 40) // len(choices)
                            option_h = ch - 60
                            hit = False
                            for i, key in enumerate(choices):
                                ox = panel_rect.x + 20 + i * option_w
                                oy = panel_rect.y + 48
                                rect = pygame.Rect(ox, oy, option_w - 8, option_h)
                                if rect.collidepoint(mx, my):
                                    player.apply_subitem_choice(key)
                                    try:
                                        for _ in range(8):
                                            particles.append(DeathParticle(player.x, player.y, CYAN))
                                    except Exception:
                                        pass
                                    hit = True
                                    break
                            if hit:
                                continue

                    # エンド画面のボタン処理（GAME OVER / CLEAR）
                    if (game_over or game_clear) and event.button == 1:
                        # マウス座標を仮想画面座標に変換
                        mouse_x, mouse_y = event.pos
                        virtual_x = (mouse_x - offset_x) / scale_factor if scale_factor > 0 else mouse_x
                        virtual_y = (mouse_y - offset_y) / scale_factor if scale_factor > 0 else mouse_y
                        virtual_x = max(0, min(SCREEN_WIDTH, virtual_x))
                        virtual_y = max(0, min(SCREEN_HEIGHT, virtual_y))
                        mx, my = int(virtual_x), int(virtual_y)
                        try:
                            rects = get_end_button_rects(game_clear)
                            # Continue はゲームオーバー時のみ有効
                            if game_over and rects.get('continue') and rects['continue'].collidepoint(mx, my):
                                player.hp = player.get_max_hp()
                                # コンティニュー時に3秒間の無敵時間を付与
                                player.set_special_invincible(3.0)
                                game_over = False
                                force_ended = False  # 強制終了フラグもリセット
                                for _ in range(8):
                                    particles.append(DeathParticle(player.x, player.y, CYAN))
                                continue
                            # Restart
                            if rects.get('restart') and rects['restart'].collidepoint(mx, my):
                                # セーブデータに記録
                                save_system.add_money(current_game_money + int(game_time * MONEY_PER_SURVIVAL_SECOND))
                                save_system.record_game_end(game_time, player.level, enemies_killed_this_game, player.exp)
                                # 武器使用統計も記録
                                if damage_stats:
                                    save_system.record_weapon_usage(damage_stats)
                                # 実績チェック
                                save_system.check_achievements()
                                save_system.save()
                                print(f"[INFO] Game data saved. Total money now: {save_system.get_money()}G")
                                
                                player, enemies, experience_gems, items, game_over, game_clear, spawn_timer, spawn_interval, game_time, last_difficulty_increase, particles, damage_stats, boss_spawn_timer, spawned_boss_types = init_game_state(screen, save_system)
                                try:
                                    spawn_manager = EnemySpawnManager()  # スポーンマネージャーも再初期化
                                except Exception as e:
                                    print(f"ERROR: Failed to reinitialize EnemySpawnManager: {e}")
                                    pygame.quit()
                                    sys.exit(1)
                                # リセット
                                current_game_money = 0
                                enemies_killed_this_game = 0
                                enemy_kill_stats = {}
                                boss_kill_stats = {}
                                force_ended = False  # 強制終了フラグもリセット
                                # ボックスマネージャーをリセット
                                box_manager = BoxManager()
                                # HP回復エフェクト用のコールバックを設定
                                def heal_effect_callback(x, y, heal_amount, is_auto=False):
                                    if is_auto:
                                        particles.append(AutoHealEffect(x, y))
                                    particles.append(HealEffect(x, y, heal_amount))
                                player.heal_effect_callback = heal_effect_callback
                                continue
                        except Exception:
                            pass

            # キーボードでのレベルアップ選択処理は KEYDOWN イベントで単発処理に変更済み

            # ループ冒頭でプレイヤー位置からターゲットカメラを算出（まだスムーズは適用しない）
            target_cam_x = max(0, min(WORLD_WIDTH - SCREEN_WIDTH, int(player.x - SCREEN_WIDTH // 2)))
            target_cam_y = max(0, min(WORLD_HEIGHT - SCREEN_HEIGHT, int(player.y - SCREEN_HEIGHT // 2)))

            # UI が表示されてゲームを停止すべきかを判定する。
            # フラグだけでなく、実際に候補リストが存在するかもチェックする（フラグが残留していると攻撃できなくなる不具合対策）。
            awaiting_weapon_active = bool(getattr(player, 'awaiting_weapon_choice', False) and getattr(player, 'last_level_choices', None))
            awaiting_subitem_active = bool(getattr(player, 'awaiting_subitem_choice', False) and getattr(player, 'last_subitem_choices', None))

            # UI表示中のマウス移動検出（入力メソッド切り替え用）
            if awaiting_weapon_active or awaiting_subitem_active:
                # 仮想マウス座標を取得してマウス移動検出に使用
                def get_virtual_mouse_pos_for_detection():
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    virtual_x = (mouse_x - offset_x) / scale_factor if scale_factor > 0 else mouse_x
                    virtual_y = (mouse_y - offset_y) / scale_factor if scale_factor > 0 else mouse_y
                    virtual_x = max(0, min(SCREEN_WIDTH, virtual_x))
                    virtual_y = max(0, min(SCREEN_HEIGHT, virtual_y))
                    return int(virtual_x), int(virtual_y)
                
                virtual_mouse_pos = get_virtual_mouse_pos_for_detection()
                # マウスの位置が変化した場合は入力メソッドをマウスに切り替え
                if hasattr(player, '_last_virtual_mouse_pos'):
                    if player._last_virtual_mouse_pos != virtual_mouse_pos:
                        player.set_input_method("mouse")
                player._last_virtual_mouse_pos = virtual_mouse_pos

            # ゲームの更新処理。武器/サブアイテム選択UIが開いている間はゲームを一時停止する
            if not game_over and not game_clear and not (awaiting_weapon_active or awaiting_subitem_active):
                # マウス座標変換関数を定義
                def get_virtual_mouse_pos():
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    # オフセットを引いてからスケールで割る
                    virtual_x = (mouse_x - offset_x) / scale_factor if scale_factor > 0 else mouse_x
                    virtual_y = (mouse_y - offset_y) / scale_factor if scale_factor > 0 else mouse_y
                    # 仮想画面の範囲内にクランプ
                    virtual_x = max(0, min(SCREEN_WIDTH, virtual_x))
                    virtual_y = max(0, min(SCREEN_HEIGHT, virtual_y))
                    return int(virtual_x), int(virtual_y)
                
                # プレイヤーの移動（現在のカメラ位置と仮想マウス座標を渡す）
                player.move(int(camera_x), int(camera_y), get_virtual_mouse_pos, delta_time)

                # 自動攻撃の更新（仮想マウス座標も渡す）
                player.update_attacks(enemies, camera_x=int(camera_x), camera_y=int(camera_y), get_virtual_mouse_pos=get_virtual_mouse_pos)

                # 自然回復（HPサブアイテム所持時のみ、2秒で1回復）（delta_timeを渡す）
                try:
                    player.update_regen(delta_time)
                except Exception:
                    pass

                # 無敵時間の更新（秒単位でのdelta_timeを渡す）
                delta_time_seconds = main.smoothed_delta_time_ms / 1000.0
                player.update_invincible(delta_time_seconds)

                # マグネット効果の更新
                player.update_magnet_effect()

                # 画面揺れエフェクトの更新
                player.update_screen_shake()

                # ボックスの更新処理
                current_time = pygame.time.get_ticks()
                box_manager.update(current_time, player)
                
                # ボックスと攻撃の当たり判定（敵より先にチェック）
                for box in box_manager.get_all_boxes():
                    # 落下中のボックスはスキップ
                    if box.is_dropping:
                        continue
                        
                    for attack in player.active_attacks[:]:
                        # spawn_delay によってまだ発生していない攻撃は無視する
                        if getattr(attack, '_pending', False):
                            continue
                        
                        # ボックスと攻撃の当たり判定
                        dx = abs(box.x - attack.x)
                        dy = abs(box.y - attack.y)
                        attack_range = getattr(attack, 'size', 0)
                        box_range = box.size // 2
                        total_range = attack_range + box_range
                        
                        if dx < total_range and dy < total_range:
                            # 持続系攻撃の処理
                            persistent_types = {"garlic", "holy_water"}
                            is_persistent = getattr(attack, 'type', '') in persistent_types
                            
                            # attack に必要な構造を初期化（動的に追加）
                            if not hasattr(attack, 'hit_boxes'):
                                attack.hit_boxes = set()
                            if not hasattr(attack, 'last_box_hit_times'):
                                attack.last_box_hit_times = {}
                            
                            # 非持続系は一度ヒットしたら再ヒットさせない
                            if not is_persistent:
                                if id(box) in attack.hit_boxes:
                                    continue
                            else:
                                # 持続系は最後にダメージを与えた時刻から0.2秒以上経過していれば再ダメージ
                                last = attack.last_box_hit_times.get(id(box), -999)
                                if game_time - last < 0.3:
                                    continue
                            
                            # ダメージを適用
                            dmg = getattr(attack, 'damage', 0) or 0
                            try:
                                dmg = float(dmg)
                            except Exception:
                                dmg = 0.0
                            
                            # ボックスにダメージを与える
                            destroyed = box.take_damage(dmg, player)
                            
                            # ヒット時の記録
                            if is_persistent:
                                attack.last_box_hit_times[id(box)] = game_time
                            else:
                                attack.hit_boxes.add(id(box))
                            
                            # ボックス破壊時のアイテムドロップ
                            if destroyed:
                                dropped_items = box.get_dropped_items()
                                items.extend(dropped_items)
                                
                                # 破壊エフェクト
                                for _ in range(6):
                                    particles.append(DeathParticle(box.x, box.y, (139, 69, 19)))  # 茶色の破片
                            
                            # ヒット時のエフェクト
                            particles.append(DeathParticle(box.x, box.y, (255, 255, 255)))
                            # ヒット時に消費する攻撃（弾丸系など）のみ削除する
                            consumable_on_hit = {"magic_wand"}
                            if getattr(attack, 'type', '') in consumable_on_hit:
                                if attack in player.active_attacks:
                                    player.active_attacks.remove(attack)
                            
                            # stone は貫通させるため、貫通攻撃の一覧を定義
                            penetrating_types = {"stone"}
                            if getattr(attack, 'type', '') not in penetrating_types:
                                break

                # 破壊されたボックスを削除
                box_manager.clear_destroyed_boxes()

                # 攻撃と敵の当たり判定
                for attack in player.active_attacks[:]:
                    # spawn_delay によってまだ発生していない攻撃は無視する
                    if getattr(attack, '_pending', False):
                        continue
                    for enemy in enemies[:]:
                        # 矩形当たり判定（高速化：円形より計算が軽い）
                        dx = abs(enemy.x - attack.x)
                        dy = abs(enemy.y - attack.y)
                        # 攻撃の半径 + 敵の半径で判定（従来は誤って/2していた）
                        r = getattr(attack, 'size', 0) + getattr(enemy, 'size', 0)
                        if dx < r and dy < r:
                            # 持続系攻撃は0.2秒ごとにダメージ再発生
                            persistent_types = {"garlic", "holy_water"}
                            is_persistent = getattr(attack, 'type', '') in persistent_types

                            # attack に必要な構造を初期化（動的に追加）
                            if not hasattr(attack, 'hit_targets'):
                                attack.hit_targets = set()
                            if not hasattr(attack, 'last_hit_times'):
                                attack.last_hit_times = {}

                            # 非持続系は一度ヒットしたら再ヒットさせない
                            if not is_persistent:
                                if id(enemy) in attack.hit_targets:
                                    continue
                            else:
                                # 持続系は最後にダメージを与えた時刻から適切な間隔経過していれば再ダメージ
                                last = attack.last_hit_times.get(id(enemy), -999)
                                damage_interval = 0.2  # デフォルト間隔（秒）
                                
                                # 武器タイプごとの間隔設定
                                attack_type = getattr(attack, 'type', '')
                                if attack_type == "garlic":
                                    damage_interval = GARLIC_DAMAGE_INTERVAL_MS / 1000.0  # ミリ秒から秒に変換
                                elif attack_type == "holy_water":
                                    damage_interval = HOLY_WATER_DAMAGE_INTERVAL_MS / 1000.0  # ミリ秒から秒に変換
                                
                                if game_time - last < damage_interval:
                                    continue

                            # 攻撃のダメージを適用
                            # ダメージにランダム性を追加（±10%の範囲）
                            dmg = max(0.0, float(getattr(attack, 'damage', 0)) * random.uniform(0.9, 1.1))
                            hp_before = enemy.hp
                            enemy.hp -= dmg

                            # サウンド: 敵被弾
                            # from audio import audio (先頭でインポート済み)
                            audio.play_sound('enemy_hurt')

                            # ノックバック処理
                            # 武器ごとのノックバック量を定義（元の値に戻す）
                            knockback_forces = {
                                "whip": 80.0,          # ムチ：強い
                                "magic_wand": 60.0,    # 魔法の杖：中程度
                                "axe": 120.0,          # 斧：非常に強い
                                "stone": 40.0,         # 石：弱い
                                "knife": 50.0,         # ナイフ：弱め
                                "rotating_book": 30.0, # 回転する本：弱い
                                "thunder": 100.0,      # 雷：強い
                                "garlic": 20.0,        # にんにく：很弱い
                                "holy_water": 25.0,    # 聖水：弱い
                            }
                            
                            weapon_type = getattr(attack, 'type', '')
                            knockback_force = knockback_forces.get(weapon_type, 50.0)  # デフォルト値
                            
                            # ノックバックを適用
                            if hasattr(enemy, 'apply_knockback'):
                                enemy.apply_knockback(attack.x, attack.y, knockback_force)

                            # ヒット時の記録: 非持続系は hit_targets に追加、持続系は last_hit_times を更新
                            if is_persistent:
                                attack.last_hit_times[id(enemy)] = game_time
                            else:
                                attack.hit_targets.add(id(enemy))

                            # ダメージ集計: 武器(type)ごとに合計ダメージを記録
                            atk_type = getattr(attack, 'type', 'unknown') or 'unknown'
                            damage_stats[atk_type] = damage_stats.get(atk_type, 0) + dmg
                            
                            # Garlic がヒットしたらプレイヤーを1回復する（クールダウン: 500ms）
                            if getattr(attack, 'type', '') == 'garlic':
                                now = pygame.time.get_ticks()
                                # attack にクールダウン時刻を保持
                                if not hasattr(attack, 'last_garlic_heal_time'):
                                    attack.last_garlic_heal_time = -999999
                                if now - attack.last_garlic_heal_time >= GARLIC_HEAL_INTERVAL_MS:
                                    # HPサブアイテムのレベルに応じた回復量を使用
                                    garlic_heal_amount = player.get_garlic_heal_amount()
                                    healed = player.heal(garlic_heal_amount, "garlic")
                                    if healed > 0:
                                        # from audio import audio (先頭でインポート済み)
                                        audio.play_sound('heal')
                                    attack.last_garlic_heal_time = now

                            # ヒット時の小エフェクト
                            if hasattr(enemy, 'on_hit') and callable(enemy.on_hit):
                                enemy.on_hit()

                            for _ in range(2):  # 4から2に削減
                                particles.append(DeathParticle(enemy.x, enemy.y, enemy.color))

                            # ダメージ数表示を追加（敵の上部に素早くフェードイン・アウト）
                            try:
                                dval = float(dmg)
                                if dval <= 10.0:
                                    color = WHITE
                                else:
                                    t = min(1.0, max(0.0, (dval - 10.0) / 40.0))
                                    r = 255
                                    g = int(255 - (215 * t))
                                    b = int(255 - (215 * t))
                                    color = (r, g, b)
                                particles.append(DamageNumber(enemy.x, enemy.y - enemy.size - 6, int(dmg), color=color))
                            except Exception:
                                pass

                            # 敵のHPが0以下なら死亡処理
                            if enemy.hp <= 0:
                                for _ in range(4):  # 8から4に削減
                                    particles.append(DeathParticle(enemy.x, enemy.y, enemy.color))

                                # ボス死亡時の特別エフェクト（赤いドット＋拡大赤円フラッシュ＋画面揺れ）
                                if getattr(enemy, 'is_boss', False):
                                    try:
                                        from effects.particles import BossDeathEffect, BossDeathFlash
                                        particles.append(BossDeathEffect(enemy.x, enemy.y))
                                        particles.append(BossDeathFlash(enemy.x, enemy.y))
                                        # 画面揺れ（ボム取得時と同じ）
                                        if hasattr(player, 'activate_screen_shake'):
                                            player.activate_screen_shake()
                                    except Exception as e:
                                        print(f"[WARNING] Failed to create boss death effect: {e}")

                                    # ボス撃破時に特別な宝箱 (box4.png) をドロップ
                                    try:
                                        # ItemBox は BoxManager を通じて管理されるべきなので、box_manager に追加
                                        from ui.box import ItemBox
                                        special_box = ItemBox(enemy.x, enemy.y, box_type=4)
                                        box_manager.boxes.append(special_box)
                                        # 大きめのスポーンエフェクト
                                        if len(particles) < 300:
                                            for _ in range(12):
                                                particles.append(SpawnParticle(special_box.x, special_box.y, (255, 100, 100)))
                                    except Exception as e:
                                        pass

                                # 撃破カウンターを増加
                                enemies_killed_this_game += 1
                                current_game_money += MONEY_PER_ENEMY_KILLED
                                
                                # エネミーNo.別撃破統計を更新
                                enemy_no = getattr(enemy, 'enemy_no', 1)  # デフォルトはNo.1
                                if enemy_no in enemy_kill_stats:
                                    enemy_kill_stats[enemy_no] += 1
                                else:
                                    enemy_kill_stats[enemy_no] = 1
                                
                                # ボス撃破統計を更新（ボスの場合）
                                is_boss = getattr(enemy, 'is_boss', False)
                                if is_boss:
                                    boss_no = getattr(enemy, 'boss_no', 1)  # デフォルトはボスNo.1
                                    if boss_no in boss_kill_stats:
                                        boss_kill_stats[boss_no] += 1
                                    else:
                                        boss_kill_stats[boss_no] = 1

                                # エネミーからは100%経験値ジェムのみドロップ
                                experience_gems.append(ExperienceGem(enemy.x, enemy.y))
                                enforce_experience_gems_limit(experience_gems, player_x=player.x, player_y=player.y)

                                if enemy in enemies:
                                    enemies.remove(enemy)

                            # ヒット時に消費する攻撃（弾丸系など）のみ削除する
                            consumable_on_hit = {"magic_wand"}
                            if getattr(attack, 'type', '') in consumable_on_hit:
                                if attack in player.active_attacks:
                                    player.active_attacks.remove(attack)

                            # stone は貫通させるため、貫通攻撃の一覧を定義
                            penetrating_types = {"stone"}
                            if getattr(attack, 'type', '') not in penetrating_types:
                                break

                # ゲーム時間の更新（デルタタイムベース）
                # フレームスキップが発生してもゲーム時間は正確に進む
                frame_time_seconds = TARGET_FRAME_TIME / 1000.0
                game_time_accumulator += main.smoothed_delta_time_ms / 1000.0  # ミリ秒を秒に変換
                
                # 固定タイムステップでゲーム進行（フレームスキップ対応）
                updates_needed = int(game_time_accumulator / frame_time_seconds)
                if updates_needed > 0:
                    game_time += updates_needed * frame_time_seconds
                    game_time_accumulator -= updates_needed * frame_time_seconds

                # クリア判定
                if game_time >= SURVIVAL_TIME:
                    game_clear = True

                # 15秒ごとに難易度アップ（間隔を短縮）
                if game_time - last_difficulty_increase >= 15:
                    spawn_interval = max(10, spawn_interval - 5)
                    last_difficulty_increase = game_time

                # ボス生成処理（CSVの各行を個別チェック）
                boss_spawn_timer += 1
                
                # 全てのボス設定を取得
                all_boss_configs = Enemy.get_all_boss_configs()
                
                # Noベースでボス設定を処理
                for key, boss_config in all_boss_configs.items():
                    # Noベースのエントリのみを処理
                    if not isinstance(key, int):
                        continue
                    
                    boss_no = key
                    boss_type = boss_config['type']
                    level = boss_config['level']
                    spawn_time = boss_config['spawn_time']
                    spawn_time_frames = spawn_time * 60  # 秒をフレームに変換
                    
                    # 指定時間に達したら1回だけスポーン（既にスポーン済みでない場合）
                    should_spawn = False
                    if game_time * 60 >= spawn_time_frames:  # 指定時間を過ぎている
                        # この特定のNoのボスがまだスポーンしていない場合
                        if boss_no not in spawned_boss_types:
                            should_spawn = True
                    
                    if should_spawn:
                            
                            # ボスを画面外からスポーン（軽量化版）
                            screen_margin = 150
                            attempts = 0
                            max_attempts = 3  # ボスは試行回数をさらに削減
                            boss_x, boss_y = None, None
                            
                            while attempts < max_attempts and boss_x is None:
                                side = random.randint(0, 3)
                                
                                if side == 0:  # 上から
                                    boss_x = max(50, min(WORLD_WIDTH - 50, player.x + random.randint(-SCREEN_WIDTH//2, SCREEN_WIDTH//2)))
                                    boss_y = max(50, player.y - SCREEN_HEIGHT//2 - screen_margin - random.randint(0, 50))
                                elif side == 1:  # 右から
                                    boss_x = min(WORLD_WIDTH - 50, player.x + SCREEN_WIDTH//2 + screen_margin + random.randint(0, 50))
                                    boss_y = max(50, min(WORLD_HEIGHT - 50, player.y + random.randint(-SCREEN_HEIGHT//2, SCREEN_HEIGHT//2)))
                                elif side == 2:  # 下から
                                    boss_x = max(50, min(WORLD_WIDTH - 50, player.x + random.randint(-SCREEN_WIDTH//2, SCREEN_WIDTH//2)))
                                    boss_y = min(WORLD_HEIGHT - 50, player.y + SCREEN_HEIGHT//2 + screen_margin + random.randint(0, 50))
                                else:  # 左から
                                    boss_x = max(50, player.x - SCREEN_WIDTH//2 - screen_margin - random.randint(0, 50))
                                    boss_y = max(50, min(WORLD_HEIGHT - 50, player.y + random.randint(-SCREEN_HEIGHT//2, SCREEN_HEIGHT//2)))
                                
                                # 境界チェック
                                if not (50 <= boss_x <= WORLD_WIDTH - 50 and 50 <= boss_y <= WORLD_HEIGHT - 50):
                                    boss_x = None
                                    attempts += 1
                                else:
                                    break
                            
                            # フォールバック
                            if boss_x is None:
                                boss_x = max(50, min(WORLD_WIDTH - 50, WORLD_WIDTH // 2))
                                boss_y = max(50, min(WORLD_HEIGHT - 50, WORLD_HEIGHT // 2))
                            
                            # ステージを考慮して安全な位置を探す（軽量化）
                            if stage_map:
                                boss_x, boss_y = stage_map.find_safe_spawn_position(boss_x, boss_y, 50)
                            
                            # ボス生成（NoベースでCSVの設定に基づき）
                            boss = Enemy(screen, game_time, spawn_x=boss_x, spawn_y=boss_y, is_boss=True, boss_type=boss_type, boss_image_file=boss_config['image_file'], boss_no=boss_no)
                            enemies.append(boss)
                            
                            # この特定のNoのボスを出現済みリストに追加
                            spawned_boss_types.add(boss_no)
                            
                            # ボススポーンエフェクト（軽量化）
                            if len(particles) < 300:
                                for _ in range(6):  # スパイクを抑える
                                    particles.append(SpawnParticle(boss_x, boss_y, (255, 215, 0)))  # 金色

                # 敵の生成を爆発的に
                # spawn_frequency倍率を適用してスポーン頻度を調整
                frequency_multiplier = spawn_manager.get_average_spawn_frequency(game_time)
                spawn_timer += frequency_multiplier  # 倍率を適用
                
                if spawn_timer >= spawn_interval:
                    if game_time <= 30:
                        num_enemies = 1 + int(game_time // 10)
                    else:
                        base_enemies = 1 + int((game_time - 30) // 20)
                        num_enemies = base_enemies + int((game_time ** 1.2) / 15)

                    if game_time > SURVIVAL_TIME * 0.7:
                        num_enemies = int(num_enemies * 1.2)  # 1.3から1.2に削減

                    num_enemies = min(num_enemies, 8)  # 12から8に削減

                    for _ in range(num_enemies):
                        cam_vx = int(camera_x)
                        cam_vy = int(camera_y)
                        margin = 64
                        
                        # 軽量化：候補を生成せず、直接有効な位置を計算
                        attempts = 0
                        max_attempts = 5  # 最大試行回数を大幅削減
                        sx, sy = None, None
                        
                        while attempts < max_attempts and sx is None:
                            side = random.randint(0, 3)
                            
                            if side == 0:  # 上側
                                sx = random.randint(max(50, cam_vx - margin), min(WORLD_WIDTH - 50, cam_vx + SCREEN_WIDTH + margin))
                                sy = max(50, cam_vy - margin - random.randint(0, 50))
                            elif side == 1:  # 右側
                                sx = min(WORLD_WIDTH - 50, cam_vx + SCREEN_WIDTH + margin + random.randint(0, 50))
                                sy = random.randint(max(50, cam_vy - margin), min(WORLD_HEIGHT - 50, cam_vy + SCREEN_HEIGHT + margin))
                            elif side == 2:  # 下側
                                sx = random.randint(max(50, cam_vx - margin), min(WORLD_WIDTH - 50, cam_vx + SCREEN_WIDTH + margin))
                                sy = min(WORLD_HEIGHT - 50, cam_vy + SCREEN_HEIGHT + margin + random.randint(0, 50))
                            else:  # 左側
                                sx = max(50, cam_vx - margin - random.randint(0, 50))
                                sy = random.randint(max(50, cam_vy - margin), min(WORLD_HEIGHT - 50, cam_vy + SCREEN_HEIGHT + margin))
                            
                            # 境界チェック
                            if not (50 <= sx <= WORLD_WIDTH - 50 and 50 <= sy <= WORLD_HEIGHT - 50):
                                sx = None  # 無効な位置の場合は再試行
                                attempts += 1
                            else:
                                break
                        
                        # フォールバック
                        if sx is None:
                            sx = random.randint(max(50, cam_vx), min(WORLD_WIDTH - 50, cam_vx + SCREEN_WIDTH))
                            sy = random.randint(max(50, cam_vy), min(WORLD_HEIGHT - 50, cam_vy + SCREEN_HEIGHT))

                        # ステージを考慮して安全な位置を探す（軽量化）
                        if stage_map:
                            sx, sy = stage_map.find_safe_spawn_position(sx, sy, 32)

                        # 時間に応じたランダムなenemy_noと倍率を選択
                        enemy_no, rule = spawn_manager.select_enemy_no(game_time)
                        strength_mult, size_mult = spawn_manager.get_enemy_modifiers(rule)
                        
                        enemy = Enemy(screen, game_time, spawn_x=sx, spawn_y=sy, spawn_side=side, 
                                     enemy_no=enemy_no, strength_multiplier=strength_mult, size_multiplier=size_mult)
                        enemies.append(enemy)
                        particles.append(SpawnParticle(enemy.x, enemy.y, enemy.color))
                    spawn_timer = 0

                # 敵の数を制限（バランス調整）
                # プレイヤーレベルに応じて制限を調整
                BASE_MAX_ENEMIES = 100  # 元の数に戻す
                LEVEL_SCALING = min(20, player.level * 2)  # レベルスケーリングも元に戻す
                MAX_ENEMIES = BASE_MAX_ENEMIES + LEVEL_SCALING
                
                if len(enemies) > MAX_ENEMIES:
                    # ボスは削除対象から除外
                    regular_enemies = [e for e in enemies if not getattr(e, 'is_boss', False)]
                    boss_enemies = [e for e in enemies if getattr(e, 'is_boss', False)]
                    
                    # 通常エネミーのみで制限チェック
                    if len(regular_enemies) > MAX_ENEMIES:
                        # 画面外の敵を優先的に削除（画面内の敵は絶対に保護）
                        enemies_to_remove = len(regular_enemies) - MAX_ENEMIES
                        
                        # 画面外の敵を特定して優先的に削除（より大きなマージンで確実に保護）
                        off_screen_enemies = []
                        on_screen_enemies = []
                        
                        for enemy in regular_enemies:
                            # 適切なマージンで視界内の敵を保護
                            if enemy.is_in_screen_bounds(player, screen_width=SCREEN_WIDTH, screen_height=SCREEN_HEIGHT, margin=200):
                                on_screen_enemies.append(enemy)
                            else:
                                off_screen_enemies.append(enemy)
                        
                        # 画面外の敵から削除
                        removed = 0
                        while removed < enemies_to_remove and off_screen_enemies:
                            off_screen_enemies.pop(0)
                            removed += 1
                        
                        # まだ削除が必要な場合のみ画面内の敵から削除（古い順）
                        # リストを再構築（ボスを含める）
                        enemies[:] = boss_enemies + on_screen_enemies + off_screen_enemies

                # 削除対象の敵を記録するリスト
                enemies_to_remove = []
                # 画面外に出た通常エネミーを即時リポップするためのキュー
                new_enemies_to_add = []

                # --- ユニフォームグリッドによる近傍検索構築 ---
                # 近傍探索の対象を隣接セルに限定して separation の計算コストを削減
                try:
                    # セルサイズは敵サイズや視界に合わせて調整可能
                    GRID_CELL_SIZE = 128
                    grid = {}
                    for e in enemies:
                        try:
                            gx = int(e.x) // GRID_CELL_SIZE
                            gy = int(e.y) // GRID_CELL_SIZE
                        except Exception:
                            gx, gy = 0, 0
                        key = (gx, gy)
                        grid.setdefault(key, []).append(e)
                except Exception:
                    grid = None

                # エネミー移動処理（並列化対応・高精度パフォーマンス測定付き）
                enemy_update_start_time = time.perf_counter()
                
                if len(enemies) > 2 and PARALLEL_PROCESSING_ENABLED:  # 閾値を5から2に大幅に下げる（より積極的な並列化）
                    # 大量のエネミーの場合は並列処理
                    try:
                        # エネミーを複数バッチに分割
                        batch_size = max(1, len(enemies) // 8)  # 8つのバッチに分割（6→8に増加）
                        enemy_batches = [enemies[i:i + batch_size] for i in range(0, len(enemies), batch_size)]
                        
                        num_workers = min(8, len(enemy_batches), mp.cpu_count())  # 8コアをフル活用
                        performance_stats['parallel_threads'] = max(performance_stats.get('parallel_threads', 0), num_workers)
                        with ThreadPoolExecutor(max_workers=num_workers) as executor:  # 最大8スレッド
                            def update_enemy_batch(enemy_batch):
                                for enemy in enemy_batch:
                                    try:
                                        # ノックバック更新処理
                                        if hasattr(enemy, 'update_knockback'):
                                            # delta_timeをframe_timeとして渡す（1/60秒を基準としたframe time）
                                            enemy.update_knockback(delta_time * (1.0/60.0))
                                        
                                        # 簡素化された近傍処理
                                        nearby = enemies if len(enemies) <= 50 else enemy_batch
                                        enemy.move(player, camera_x=int(camera_x), camera_y=int(camera_y), map_loader=map_loader, enemies=nearby, delta_time=delta_time)
                                        
                                        # ボスの画面外チェック
                                        if hasattr(enemy, 'is_boss') and enemy.is_boss:
                                            if hasattr(enemy, 'is_boss_off_screen') and enemy.is_boss_off_screen():
                                                pass  # リスポーン処理は後で実行
                                    except Exception:
                                        pass  # エラー時は個々のエネミーをスキップ
                            
                            # 並列実行
                            futures = [executor.submit(update_enemy_batch, batch) for batch in enemy_batches]
                            for future in futures:
                                future.result()  # 完了を待つ
                                
                    except Exception:
                        # 並列処理エラー時は逐次処理にフォールバック
                        for enemy in enemies[:]:
                            if hasattr(enemy, 'update_knockback'):
                                enemy.update_knockback(delta_time * (1.0/60.0))
                            nearby = enemies
                            enemy.move(player, camera_x=int(camera_x), camera_y=int(camera_y), map_loader=map_loader, enemies=nearby, delta_time=delta_time)
                else:
                    # 少数のエネミーまたは並列処理無効の場合は従来の処理
                    for enemy in enemies[:]:
                        # ノックバック更新処理
                        if hasattr(enemy, 'update_knockback'):
                            enemy.update_knockback(delta_time * (1.0/60.0))
                        # 近傍リスト構築の大幅軽量化（動作は維持）
                        nearby = enemies  # デフォルトは全エネミー
                        if grid is not None and len(enemies) > 50:  # 閾値を下げて早期適用
                            try:
                                gx = int(enemy.x) // GRID_CELL_SIZE
                                gy = int(enemy.y) // GRID_CELL_SIZE
                                # より効率的なグリッド検索（計算量削減）
                                nearby_set = []
                                nearby_set.extend(grid.get((gx, gy), []))  # 中心セルのみ
                                # エネミー数が多い場合のみ周辺セルを追加
                                if len(enemies) > 100:
                                    for ox, oy in [(gx-1, gy), (gx+1, gy), (gx, gy-1), (gx, gy+1)]:  # 十字のみ
                                        nearby_set.extend(grid.get((ox, oy), []))
                                nearby = nearby_set if len(nearby_set) < len(enemies) // 2 else enemies
                            except Exception:
                                nearby = enemies

                        enemy.move(player, camera_x=int(camera_x), camera_y=int(camera_y), map_loader=map_loader, enemies=nearby, delta_time=delta_time)
                
                # ボスの画面外チェックとリスポーン処理（全エネミーをチェック）
                for enemy in enemies[:]:
                    if hasattr(enemy, 'is_boss') and enemy.is_boss:
                        if hasattr(enemy, 'is_boss_off_screen') and enemy.is_boss_off_screen():
                            # ボスを画面外からランダムにリスポーン（HPは維持）
                            enemy.respawn_boss_randomly(player)
                            
                            # リスポーンエフェクト
                            if len(particles) < 300:
                                for _ in range(10):
                                    particles.append(SpawnParticle(enemy.x, enemy.y, (255, 215, 0)))  # 金色

                # 敵の攻撃処理（動作継続、頻度調整で軽量化）
                for enemy in enemies[:]:
                    # パフォーマンス重視：攻撃更新頻度をより積極的に制限
                    # CPU使用率に応じて動的に調整
                    cpu_usage = performance_stats.get('cpu_usage', 50.0)
                    attack_should_update = True
                    
                    if cpu_usage > 80.0:  # CPU使用率が80%超過時は大幅に頻度を下げる
                        if len(enemies) > 100:
                            attack_should_update = (frame_count % 16 == 0)  # 1/16頻度
                        elif len(enemies) > 50:
                            attack_should_update = (frame_count % 12 == 0)  # 1/12頻度
                        else:
                            attack_should_update = (frame_count % 8 == 0)   # 1/8頻度
                    elif cpu_usage > 65.0:  # CPU使用率が65%超過時は頻度を下げる
                        if len(enemies) > 100:
                            attack_should_update = (frame_count % 12 == 0)  # 1/12頻度
                        elif len(enemies) > 50:
                            attack_should_update = (frame_count % 8 == 0)   # 1/8頻度
                        else:
                            attack_should_update = (frame_count % 6 == 0)   # 1/6頻度
                    else:  # 通常時
                        if enemy.is_off_screen():
                            # 画面外は頻度を下げる
                            if len(enemies) > 100:
                                attack_should_update = (frame_count % 8 == 0)  # 1/8頻度
                            else:
                                attack_should_update = (frame_count % 4 == 0)  # 1/4頻度
                        elif len(enemies) > 150:
                            attack_should_update = (frame_count % 6 == 0)   # 1/6頻度
                        elif len(enemies) > 100:
                            attack_should_update = (frame_count % 4 == 0)   # 1/4頻度
                    
                    if attack_should_update:
                        enemy.update_attack(player)
                    
                    # 弾丸更新は常に実行（ゲームプレイの重要な要素なので軽量化対象から除外）
                    enemy.update_projectiles(player, delta_time)

                    # --- 画面外リポップ仕様: ノーマルエネミーがカメラ外（マージン付き）に出たら削除して
                    #     画面外からポップする形で再出現させる（ボスは除外） ---
                    try:
                        if not getattr(enemy, 'is_boss', False):
                            # カメラ境界にマージンを追加して判定
                            cam_left = int(camera_x) - OFFSCREEN_MARGIN
                            cam_right = int(camera_x) + SCREEN_WIDTH + OFFSCREEN_MARGIN
                            cam_top = int(camera_y) - OFFSCREEN_MARGIN
                            cam_bottom = int(camera_y) + SCREEN_HEIGHT + OFFSCREEN_MARGIN

                            if (enemy.x < cam_left or enemy.x > cam_right or
                                enemy.y < cam_top or enemy.y > cam_bottom):
                                # 削除予定に入れる
                                enemies_to_remove.append(enemy)

                                # 画面外（カメラ端の外側）から出現するように生成位置を決定
                                side = random.randint(0, 3)  # 0:上,1:右,2:下,3:左
                                if side == 0:  # 上
                                    sx = random.randint(int(camera_x) - OFFSCREEN_MARGIN, int(camera_x) + SCREEN_WIDTH + OFFSCREEN_MARGIN)
                                    sy = int(camera_y) - OFFSCREEN_MARGIN
                                elif side == 1:  # 右
                                    sx = int(camera_x) + SCREEN_WIDTH + OFFSCREEN_MARGIN
                                    sy = random.randint(int(camera_y) - OFFSCREEN_MARGIN, int(camera_y) + SCREEN_HEIGHT + OFFSCREEN_MARGIN)
                                elif side == 2:  # 下
                                    sx = random.randint(int(camera_x) - OFFSCREEN_MARGIN, int(camera_x) + SCREEN_WIDTH + OFFSCREEN_MARGIN)
                                    sy = int(camera_y) + SCREEN_HEIGHT + OFFSCREEN_MARGIN
                                else:  # 左
                                    sx = int(camera_x) - OFFSCREEN_MARGIN
                                    sy = random.randint(int(camera_y) - OFFSCREEN_MARGIN, int(camera_y) + SCREEN_HEIGHT + OFFSCREEN_MARGIN)

                                # ワールド境界をクランプ
                                sx = max(50, min(WORLD_WIDTH - 50, sx))
                                sy = max(50, min(WORLD_HEIGHT - 50, sy))

                                # 時間に応じたランダムなenemy_noと倍率を選択
                                enemy_no, rule = spawn_manager.select_enemy_no(game_time)
                                strength_mult, size_mult = spawn_manager.get_enemy_modifiers(rule)
                                # 生成は画面外から行うので spawn_x/spawn_y のみ渡す
                                new_enemies_to_add.append(Enemy(screen, game_time, spawn_x=sx, spawn_y=sy, 
                                                               enemy_no=enemy_no, strength_multiplier=strength_mult, size_multiplier=size_mult))
                                # この敵は以降の削除チェックをスキップ
                                continue
                    except Exception:
                        pass
                    
                    # 削除条件チェック（ボス以外のみ）
                    if not getattr(enemy, 'is_boss', False):
                        # 跳ね返りタイプ（タイプ2）は画面外削除しない
                        # 他のタイプで画面外に出た場合のチェックは後で追加
                        
                        # 生存時間による削除チェック（固定砲台・距離保持射撃用）
                        if enemy.should_be_removed_by_time():
                            enemies_to_remove.append(enemy)
                            continue
                        
                        # プレイヤーの視界外に十分離れた敵を削除（パフォーマンス向上）
                        # 画面範囲内の敵は絶対に削除しない（適切なマージンで保護）
                        if not enemy.is_in_screen_bounds(player, screen_width=SCREEN_WIDTH, screen_height=SCREEN_HEIGHT, margin=300):
                            # 画面外の敵のみ距離による削除を適用
                            # 行動パターン別削除条件:
                            # 1.追跡: 8000px（通常マージン）
                            # 2.直進: 9000px（画面外削除と併用）
                            # 3.距離保持: 15000px（45秒時間制限と併用）
                            # 4.固定砲台: 18000px（30秒時間制限と併用）
                            if enemy.behavior_type == 1:  # 追跡タイプ
                                delete_margin = 8000
                            elif enemy.behavior_type == 2:  # 直進タイプ
                                delete_margin = 9000
                            elif enemy.behavior_type == 3:  # 距離保持射撃
                                delete_margin = 15000
                            elif enemy.behavior_type == 4:  # 固定砲台
                                delete_margin = 18000
                            else:
                                delete_margin = 8000  # デフォルト
                            
                            if enemy.is_far_from_player(player, margin=delete_margin):
                                enemies_to_remove.append(enemy)
                                continue
                
                # 削除対象の敵を一括削除
                for enemy in enemies_to_remove:
                    if enemy in enemies:
                        enemies.remove(enemy)
                # キューされた新しい敵を追加
                if new_enemies_to_add:
                    enemies.extend(new_enemies_to_add)
                
                # 残った敵の当たり判定処理
                for enemy in enemies:
                    # 削除対象に含まれている敵はスキップ
                    if enemy in enemies_to_remove:
                        continue
                        
                    # プレイヤーとの正方形当たり判定（最高速化）
                    # プレイヤーと敵の境界ボックスが重なるかチェック
                    player_half = getattr(player, 'size', 0) // 2
                    enemy_half = getattr(enemy, 'size', 0) // 2
                    if (abs(player.x - enemy.x) < player_half + enemy_half and 
                        abs(player.y - enemy.y) < player_half + enemy_half):
                        # 無敵時間チェック（最優先）
                        if not player.can_take_damage():
                            continue  # 無敵時間中はダメージも回避も発生しない
                        
                        if random.random() < player.get_avoidance():
                            # サブアイテムスピードアップ効果で攻撃を回避
                            particles.append(AvoidanceParticle(player.x, player.y))
                            try:
                                from effects.particles import LuckyText
                                particles.append(LuckyText(player.x, player.y - getattr(player, 'size', 32) - 6, "Lukey!", color=CYAN))
                            except Exception:
                                pass
                        else:
                            # ダメージ処理
                            particles.append(HurtFlash(player.x, player.y, size=player.size))

                            # サブアイテムアーマーの効果でダメージを軽減
                            try:
                                damage = max(1, int(enemy.damage - player.get_defense()))
                                player.hp -= damage
                            except Exception:
                                player.hp -= enemy.damage

                            # 被弾時刻を更新（新しいシステムで管理）
                            player.last_hit_time = pygame.time.get_ticks()
                            
                            # 通常無敵時間を設定（連続ダメージ防止）
                            player.set_normal_invincible()

                            # サウンド: プレイヤー被弾
                            try:
                                # from audio import audio (先頭でインポート済み)
                                audio.play_sound('player_hurt')
                            except Exception:
                                pass

                            # エネミーは削除しない（継続して存在）
                            # if not getattr(enemy, 'is_boss', False):
                            #     enemies.remove(enemy)
                            if player.hp <= 0:
                                game_over = True
                                # try:
                                #     if not getattr(enemy, 'is_boss', False):
                                #         enemies.remove(enemy)
                                # except Exception:
                                #     pass

                # 敵の弾丸とプレイヤーの衝突判定（負荷軽減）
                # エネミー弾丸処理（効率化：事前計算）
                total_projectiles = sum(len(enemy.get_projectiles()) for enemy in enemies)
                
                # エネミー更新処理の時間を記録（高精度）
                enemy_update_end_time = time.perf_counter()
                performance_stats['enemy_update_time'] = (enemy_update_end_time - enemy_update_start_time) * 1000  # ms変換
                
                # 弾丸数が多い場合はより厳しく制限
                if total_projectiles > 150:
                    enemy_limit = max(1, len(enemies) // 4)  # 1/4まで削減
                elif total_projectiles > 100:
                    enemy_limit = max(1, len(enemies) // 3)  # 1/3まで削減
                elif total_projectiles > 50:
                    enemy_limit = max(1, len(enemies) * 2 // 3)
                else:
                    enemy_limit = len(enemies)
                
                # プレイヤーサイズの事前計算（重複計算削除）
                player_half = getattr(player, 'size', 0) // 2
                
                for enemy in enemies[:enemy_limit]:
                    projectiles = enemy.get_projectiles()
                    # 弾丸数による厳格制限
                    if total_projectiles > 150:
                        projectile_limit = min(5, len(projectiles))  # 大幅制限
                    elif total_projectiles > 100:
                        projectile_limit = min(8, len(projectiles))
                    else:
                        projectile_limit = min(10, len(projectiles))
                    
                    for projectile in projectiles[:projectile_limit]:
                        # プレイヤーとの正方形衝突判定（事前計算済みを使用）
                        proj_half = projectile.size // 2
                        if (abs(player.x - projectile.x) < player_half + proj_half and 
                            abs(player.y - projectile.y) < player_half + proj_half):
                                # 無敵時間チェック（最優先）
                                if not player.can_take_damage():
                                    continue  # 無敵時間中はダメージも回避も発生しない
                                
                                if random.random() < player.get_avoidance():
                                    # 攻撃を回避
                                    particles.append(AvoidanceParticle(player.x, player.y))
                                    try:
                                        from effects.particles import LuckyText
                                        particles.append(LuckyText(player.x, player.y - getattr(player, 'size', 32) - 6, "Lukey!", color=CYAN))
                                    except Exception:
                                        pass
                                else:
                                    # ダメージ処理
                                    particles.append(HurtFlash(player.x, player.y, size=player.size))

                                    # ダメージを適用
                                    try:
                                        player.hp -= max(1, int(projectile.damage - player.get_defense()))
                                    except Exception:
                                        player.hp -= projectile.damage

                                    # 被弾時刻を更新（新しいシステムで管理）
                                    player.last_hit_time = pygame.time.get_ticks()
                                    
                                    # 通常無敵時間を設定（連続ダメージ防止）
                                    player.set_normal_invincible()

                                    # サウンド: プレイヤー被弾（弾）
                                    try:
                                        # from audio import audio (先頭でインポート済み)
                                        audio.play_sound('player_hurt')
                                    except Exception:
                                        pass

                                    if player.hp <= 0:
                                        game_over = True
                                
                                # 弾丸を削除
                                enemy.projectiles.remove(projectile)
                                continue  # 弾丸が削除されたので次の弾丸へ
                            
                        # 弾丸とプレイヤーの武器の衝突判定（ボスの弾は相殺不可）
                        projectile_hit = False
                        if not getattr(projectile, 'is_boss_bullet', False):  # ボスの弾でない場合のみ相殺可能
                            for attack in player.active_attacks:
                                if projectile_hit:
                                    break
                                
                                # 武器と弾丸の正方形衝突判定（最高速化）
                                attack_half = getattr(attack, 'size', 0) // 2
                                proj_half = projectile.size // 2
                                
                                if (abs(attack.x - projectile.x) < attack_half + proj_half and 
                                    abs(attack.y - projectile.y) < attack_half + proj_half):
                                    # 武器が弾丸を迎撃
                                    projectile_hit = True
                                    break
                        
                        if projectile_hit:
                            # 弾丸迎撃エフェクトを追加
                            particles.append(DeathParticle(projectile.x, projectile.y, (255, 255, 100)))  # 黄色いエフェクト
                            
                            # 弾丸を削除
                            enemy.projectiles.remove(projectile)

                # 経験値ジェム処理（効率化：ループ外事前計算）
                gems_collected_this_frame = 0  # このフレームで取得したジェム数
                
                # ⚡ 最適化：ループ外で1回だけ計算
                player_half = getattr(player, 'size', 0) // 2
                extra_range = int(player.get_gem_pickup_range()) if hasattr(player, 'get_gem_pickup_range') else 0
                attraction_range = BASE_ATTRACTION_DISTANCE + extra_range
                attraction_range_squared = attraction_range * attraction_range
                
                for gem in experience_gems[:]:
                    # ジェムの寿命チェック（引き寄せ中でない場合のみ）
                    if hasattr(gem, 'is_expired') and gem.is_expired() and not getattr(gem, 'being_attracted', False):
                        experience_gems.remove(gem)
                        continue
                    
                    gem.move_to_player(player)
                    
                    # 🎯 最適化：ジェム個別の計算のみ
                    gem_half = getattr(gem, 'size', 0) // 2
                    pickup_range = player_half + gem_half
                    pickup_range_squared = pickup_range * pickup_range
                    
                    # 距離計算（平方根なしユークリッド距離）
                    dx = player.x - gem.x
                    dy = player.y - gem.y
                    distance_squared = dx * dx + dy * dy
                    
                    # 引き寄せ範囲に入ったら引き寄せ開始（事前計算済み）
                    if distance_squared < attraction_range_squared:
                        if not getattr(gem, 'being_attracted', False):
                            gem.being_attracted = True
                    
                    # 実際の取得範囲（プレイヤーアイコンサイズ）に到達したら取得完了
                    if distance_squared < pickup_range_squared:
                        prev_level = player.level
                        # ジェムごとの価値を付与
                        player.add_exp(getattr(gem, 'value', 1))
                        experience_gems.remove(gem)
                        gems_collected_this_frame += 1  # 取得数をカウント
                        if player.level > prev_level:
                            particles.append(LevelUpEffect(player.x, player.y))
                            for _ in range(12):
                                particles.append(DeathParticle(player.x, player.y, CYAN))
                            # レベルアップボーナス
                            current_game_money += MONEY_PER_LEVEL_BONUS
                
                # ジェム取得音声（このフレームで1つ以上取得した場合のみ1回再生）
                if gems_collected_this_frame > 0:
                    try:
                        # from audio import audio (先頭でインポート済み)
                        # constants.pyのDEFAULT_SFX_VOLUME（0.1）を使用して音量を統一
                        # min_intervalを短めに設定してレスポンスを良くする
                        audio.play_sound('gem_pickup', min_interval=0.1)
                    except Exception:
                        pass

                # アイテム処理（効率化：ループ外事前計算）
                # ⚡ 最適化：ループ外で1回だけ計算（ジェム処理と共通化）
                for item in items[:]:
                    item.move_to_player(player)
                    
                    # 🎯 最適化：アイテム個別の計算のみ
                    item_half = getattr(item, 'size', 0) // 2
                    pickup_range = player_half + item_half
                    pickup_range_squared = pickup_range * pickup_range
                    
                    # 距離計算（平方根なしユークリッド距離）
                    dx = player.x - item.x
                    dy = player.y - item.y
                    distance_squared = dx * dx + dy * dy
                    
                    # 引き寄せ範囲に入ったら引き寄せ開始（事前計算済み）
                    if distance_squared < attraction_range_squared:
                        if not getattr(item, 'being_attracted', False):
                            item.being_attracted = True
                    
                    # 実際の取得範囲に到達したら取得完了
                    if distance_squared < pickup_range_squared:
                        if item.type == "heal":
                            # 体力回復（割合回復）
                            player.heal(HEAL_ITEM_AMOUNT, "item")
                        elif item.type == "bomb":
                            # ボムアイテム効果処理（100ダメージ）
                            handle_bomb_item_effect(enemies, experience_gems, particles, player.x, player.y, player)
                        elif item.type == "magnet":
                            # マグネット効果を有効化
                            player.activate_magnet()
                        elif item.type == "money":
                            # お金を獲得
                            money_amount = getattr(item, 'amount', 10)
                            money_type = getattr(item, 'money_type', 'money1')
                            current_game_money += money_amount
                            # お金取得のエフェクト（金色の爆発）
                            for _ in range(3):
                                particles.append(DeathParticle(item.x, item.y, (255, 215, 0)))
                        items.remove(item)

            # パーティクルの更新と描画
            # パーティクルはカメラに依存しないため従来通り呼び出す
            # パーティクル数が多すぎる場合は古いものから削減して負荷を抑える
            if len(particles) > PARTICLE_LIMIT:
                # 最も新しいものを残す（古いものは削除）
                particles = particles[-PARTICLE_TRIM_TO:]

            # パーティクル更新処理（2フレームに1回で負荷軽減）
            if frame_count % 2 == 0:
                # 安全に順次更新して生存するものだけ残す
                new_particles = []
                for p in particles:
                    try:
                        if p.update():
                            new_particles.append(p)
                    except Exception:
                        # エフェクトの update で例外が出てもゲームを継続する
                        pass
                # パーティクルの更新（高精度パフォーマンス測定付き）
                particle_start_time = time.perf_counter()
                particles = parallel_update_particles(particles)
                particle_end_time = time.perf_counter()
                performance_stats['particle_update_time'] = (particle_end_time - particle_start_time) * 1000  # ms変換

            # カメラ目標を現在のプレイヤー位置から再計算（プレイヤー移動後）
            # 仮想画面サイズ（常に1280x720）を基準にカメラ計算
            desired_x = max(0, min(WORLD_WIDTH - SCREEN_WIDTH, player.x - SCREEN_WIDTH // 2))
            desired_y = max(0, min(WORLD_HEIGHT - SCREEN_HEIGHT, player.y - SCREEN_HEIGHT // 2))
            # 補間（スムージング）
            camera_x += (desired_x - camera_x) * CAMERA_LERP
            camera_y += (desired_y - camera_y) * CAMERA_LERP
            
            # 画面揺れオフセットを適用
            shake_offset_x, shake_offset_y = player.get_screen_shake_offset()
            
            # 描画で使用する整数カメラ座標（画面揺れを加味）
            int_cam_x = int(camera_x) + shake_offset_x
            int_cam_y = int(camera_y) + shake_offset_y

            # 描画処理の開始時間を記録（高精度）
            render_start_time = time.perf_counter()

            # 仮想画面をクリア
            virtual_screen.fill((0, 0, 0))

            # ワールド用サーフェスの最適化（SRCALPHA不要、convert使用）
            world_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)).convert()
            world_surf.fill((0, 0, 0))  # 背景を黒で塗りつぶし

            # 背景描画（設定により切り替え）
            if USE_CSV_MAP:
                # CSVマップ背景
                map_loader.draw_map(world_surf, int_cam_x, int_cam_y)
            else:
                # テスト用市松模様背景
                draw_test_checkerboard(world_surf, int_cam_x, int_cam_y)
            
            # 敵の描画（厳格な画面内カリング + 距離ソート最適化）
            screen_left = int_cam_x - DRAWING_MARGIN
            screen_right = int_cam_x + SCREEN_WIDTH + DRAWING_MARGIN
            screen_top = int_cam_y - DRAWING_MARGIN
            screen_bottom = int_cam_y + SCREEN_HEIGHT + DRAWING_MARGIN
            
            # 画面内エネミーのみ厳選（画面外描画を完全停止）
            screen_enemies = []
            
            for enemy in enemies:
                if (enemy.x >= screen_left and enemy.x <= screen_right and 
                    enemy.y >= screen_top and enemy.y <= screen_bottom):
                    screen_enemies.append(enemy)  # 画面内のみ
            
            # 距離ソートによる描画順最適化（近い敵を優先）
            player_x, player_y = player.x, player.y
            screen_enemies.sort(key=lambda e: (e.x - player_x) ** 2 + (e.y - player_y) ** 2)
            
            # 統計カウンタリセット
            performance_stats['draw_calls'] = 0
            performance_stats['visible_entities'] = 0
            performance_stats['culled_entities'] = len(enemies) - len(screen_enemies)
            
            # 画面内エネミーのみ描画（画面外描画を完全停止でパフォーマンス向上）
            for enemy in screen_enemies:
                enemy.draw(world_surf, int_cam_x, int_cam_y)
                enemy.draw_projectiles(world_surf, int_cam_x, int_cam_y)
                performance_stats['draw_calls'] += 2  # enemy + projectiles
                performance_stats['visible_entities'] += 1
            
            # ボックスの描画（敵の後、パーティクルの前）
            box_manager.draw_all(world_surf, int_cam_x, int_cam_y)

            # パーティクル（ワールド座標）の描画（エネミーの後、攻撃エフェクトの前に追加）
            # HurtFlash, LevelUpEffect は画面オーバーレイなので別途画面に描画する
            world_particles = [p for p in particles if not isinstance(p, (HurtFlash, LevelUpEffect))]
            overlay_particles = [p for p in particles if isinstance(p, (HurtFlash, LevelUpEffect))]
            
            # パーティクル描画数を制限（描画負荷軽減） + 視錐台カリング
            max_particles_draw = min(150, len(world_particles))  # パーティクル描画を150個まで制限
            visible_particles = []
            
            # パーティクルも画面内カリングを適用
            for particle in world_particles[:max_particles_draw]:
                if hasattr(particle, 'x') and hasattr(particle, 'y'):
                    if (particle.x >= screen_left and particle.x <= screen_right and 
                        particle.y >= screen_top and particle.y <= screen_bottom):
                        visible_particles.append(particle)
                else:
                    visible_particles.append(particle)  # 座標がない場合はそのまま描画
            
            # 画面内パーティクルのみ描画
            for particle in visible_particles:
                # 各パーティクルは world_surf 上に描画する（カメラオフセットを渡す）
                particle.draw(world_surf, int_cam_x, int_cam_y)
                performance_stats['draw_calls'] += 1
            
            # カリング統計を更新
            performance_stats['culled_entities'] += (len(world_particles[:max_particles_draw]) - len(visible_particles))
            performance_stats['visible_entities'] += len(visible_particles)

            # 経験値ジェムの描画（制限付き + 視錐台カリング）
            max_gems_draw = min(100, len(experience_gems))  # ジェム描画を100個まで制限
            visible_gems = []
            
            # ジェムも画面内カリングを適用
            for gem in experience_gems[:max_gems_draw]:
                if (gem.x >= screen_left and gem.x <= screen_right and 
                    gem.y >= screen_top and gem.y <= screen_bottom):
                    visible_gems.append(gem)
            
            # 画面内ジェムのみ描画
            for gem in visible_gems:
                gem.draw(world_surf, int_cam_x, int_cam_y)
                performance_stats['draw_calls'] += 1
            
            # カリング統計を更新
            performance_stats['culled_entities'] += (len(experience_gems[:max_gems_draw]) - len(visible_gems))
            performance_stats['visible_entities'] += len(visible_gems)

            # アイテムの描画（画面内カリングを適用）
            visible_items = []
            for item in items:
                if (item.x >= screen_left and item.x <= screen_right and 
                    item.y >= screen_top and item.y <= screen_bottom):
                    visible_items.append(item)
            
            for item in visible_items:
                item.draw(world_surf, int_cam_x, int_cam_y)
                performance_stats['draw_calls'] += 1
            
            # アイテムカリング統計を更新
            performance_stats['culled_entities'] += (len(items) - len(visible_items))
            performance_stats['visible_entities'] += len(visible_items)

            # まず武器のエフェクトを描画（プレイヤーより後ろに表示されるべきなので先に描く）
            player.draw_attacks(world_surf, int_cam_x, int_cam_y)

            # プレイヤー本体は武器エフェクトより手前に表示する
            player.draw(world_surf, int_cam_x, int_cam_y)

            # ジェム回収範囲の可視化（デバッグ用）
            if SHOW_PICKUP_RANGE:
                try:
                    pickup_range = player.get_gem_pickup_range() if hasattr(player, 'get_gem_pickup_range') else 0
                    player_screen_x = int(player.x - int_cam_x)
                    player_screen_y = int(player.y - int_cam_y)
                    
                    # 基本引き寄せ範囲（100ピクセル + サブアイテム範囲）
                    total_attraction_range = int(BASE_ATTRACTION_DISTANCE + pickup_range)
                    
                    # 実際の取得範囲（プレイヤーサイズ）
                    player_size = getattr(player, 'size', 0) // 2
                    actual_pickup_range = player_size + 4  # ジェムのサイズ考慮
                    
                    # 引き寄せ範囲を薄い緑色の円で表示（ユークリッド距離に対応）
                    pygame.draw.circle(world_surf, (0, 255, 0, 80), 
                                     (player_screen_x, player_screen_y), 
                                     total_attraction_range, 2)
                    
                    # 実際の取得範囲を濃い緑色の円で表示
                    pygame.draw.circle(world_surf, (0, 200, 0, 120), 
                                     (player_screen_x, player_screen_y), 
                                     actual_pickup_range, 1)
                except Exception:
                    pass

            # デバッグ表示: 攻撃範囲と敵の当たり判定の可視化（world_surf に描画）
            if show_debug_visuals:
                try:
                    # 攻撃エフェクトの範囲を例示（黄色い円）
                    for atk in player.active_attacks:
                        try:
                            ax = int(atk.x - int_cam_x)
                            ay = int(atk.y - int_cam_y)
                            w = int(getattr(atk, 'size_x', getattr(atk, 'size', 16) * 2))
                            h = int(getattr(atk, 'size_y', getattr(atk, 'size', 16) * 2))
                            tx = ax - w // 2
                            ty = ay - h // 2
                            s = pygame.Surface((max(1, w), max(1, h)), pygame.SRCALPHA)
                            s.fill((255, 255, 0, 40))
                            try:
                                pygame.draw.rect(s, (255, 200, 0, 180), (0, 0, w, h), 2)
                            except Exception:
                                pass
                            world_surf.blit(s, (tx, ty))
                            if debug_font:
                                t = str(getattr(atk, 'type', '?'))
                                try:
                                    txt = debug_font.render(t, True, (220, 220, 60))
                                    world_surf.blit(txt, (ax + 6, ay - 6))
                                except Exception:
                                    pass
                        except Exception:
                            pass
                    # 敵の当たり判定も表示
                    for e in enemies:
                        try:
                            ex = int(e.x - int_cam_x)
                            ey = int(e.y - int_cam_y)
                            rs = int(getattr(e, 'size', 12))
                            try:
                                pygame.draw.circle(world_surf, (255, 80, 80, 160), (ex, ey), rs, 2)
                            except Exception:
                                pygame.draw.circle(world_surf, (255, 80, 80), (ex, ey), rs, 2)
                        except Exception:
                            pass
                except Exception:
                    pass

            # ワールドを仮想画面にブリット
            virtual_screen.blit(world_surf, (0, 0))

            # オーバーレイ系パーティクルを仮想画面に直接描画（全画面フラッシュ等）
            for particle in overlay_particles:
                # overlay パーティクルはワールド座標を保持しているためカメラオフセットを渡す
                try:
                    particle.draw(virtual_screen, int_cam_x, int_cam_y)
                except TypeError:
                    particle.draw(virtual_screen)

            # 右上にミニマップを描画（毎フレーム描画でちらつき防止）
            try:
                draw_minimap(virtual_screen, player, enemies, experience_gems, items, int_cam_x, int_cam_y)
            except Exception:
                pass

            # UI描画を仮想画面に（毎フレーム描画でちらつき防止）
            draw_ui(virtual_screen, player, game_time, game_over, game_clear, damage_stats, ICONS, show_status=show_status, game_money=current_game_money, enemy_kill_stats=enemy_kill_stats, boss_kill_stats=boss_kill_stats, force_ended=force_ended)
            # エンド画面のボタンを描画（描画だけでクリックはイベントハンドラで処理）
            if game_over or game_clear:
                from ui.ui import draw_end_buttons
                draw_end_buttons(virtual_screen, game_over, game_clear, end_screen_selection)
            
            # レベルアップ候補がある場合はポップアップを ui.draw_level_choice に任せる
            # サブアイテム選択 UI を優先して表示
            if getattr(player, 'awaiting_subitem_choice', False) and getattr(player, 'last_subitem_choices', None):
                # マウス座標を仮想画面座標に変換してUI描画に渡す
                mouse_x, mouse_y = pygame.mouse.get_pos()
                virtual_mouse_x = (mouse_x - offset_x) / scale_factor if scale_factor > 0 else mouse_x
                virtual_mouse_y = (mouse_y - offset_y) / scale_factor if scale_factor > 0 else mouse_y
                virtual_mouse_x = max(0, min(SCREEN_WIDTH, virtual_mouse_x))
                virtual_mouse_y = max(0, min(SCREEN_HEIGHT, virtual_mouse_y))
                # サブアイテム選択は ui.draw_subitem_choice を使う
                from ui.ui import draw_subitem_choice
                draw_subitem_choice(virtual_screen, player, ICONS, virtual_mouse_pos=(int(virtual_mouse_x), int(virtual_mouse_y)))
            elif getattr(player, 'awaiting_weapon_choice', False) and getattr(player, 'last_level_choices', None):
                # マウス座標を仮想画面座標に変換してUI描画に渡す
                mouse_x, mouse_y = pygame.mouse.get_pos()
                virtual_mouse_x = (mouse_x - offset_x) / scale_factor if scale_factor > 0 else mouse_x
                virtual_mouse_y = (mouse_y - offset_y) / scale_factor if scale_factor > 0 else mouse_y
                virtual_mouse_x = max(0, min(SCREEN_WIDTH, virtual_mouse_x))
                virtual_mouse_y = max(0, min(SCREEN_HEIGHT, virtual_mouse_y))
                draw_level_choice(virtual_screen, player, ICONS, virtual_mouse_pos=(int(virtual_mouse_x), int(virtual_mouse_y)))

            # 仮想画面を実際の画面にスケールして転送
            screen.fill((0, 0, 0))  # レターボックス部分を黒で塗りつぶし
            
            if scale_factor != 1.0:
                # スケール済みサーフェスをキャッシュして再利用
                scaled_size = (int(SCREEN_WIDTH * scale_factor), int(SCREEN_HEIGHT * scale_factor))
                if scaled_surface is None or scaled_surface.get_size() != scaled_size:
                    # キャッシュが無効またはサイズが変わった場合のみ新しいサーフェスを作成
                    scaled_surface = pygame.Surface(scaled_size)
                    print(f"[INFO] Created scaled surface cache: {scaled_size}")
                
                # キャッシュされたサーフェスにスケールして描画（最適化版）
                pygame.transform.scale(virtual_screen, scaled_size, scaled_surface)
                screen.blit(scaled_surface, (offset_x, offset_y))
            else:
                # 等倍で描画（キャッシュ不要）
                screen.blit(virtual_screen, (offset_x, offset_y))

            # FPS表示（実画面の左下に直接描画）
            if SHOW_FPS and fps_font and len(fps_values) > 0:
                # 過去のFPS値の平均を計算
                avg_fps = sum(fps_values[-30:]) / len(fps_values[-30:])  # 直近30フレーム
                
                # 弾丸数をカウント
                total_projectiles = sum(len(enemy.get_projectiles()) for enemy in enemies)
                
                # 回収範囲情報を取得
                pickup_range = player.get_gem_pickup_range() if hasattr(player, 'get_gem_pickup_range') else 0
                pickup_level = player.get_magnet_level() if hasattr(player, 'get_magnet_level') else 0
                
                # 統計情報をまとめて表示
                fps_text = fps_font.render(f"FPS: {avg_fps:.1f} | Enemies: {len(enemies)} | Bullets: {total_projectiles} | Gems: {len(experience_gems)} | Particles: {len(particles)} | Range: {pickup_range:.1f}px (Lv{pickup_level})", True, (255, 255, 255))
                fps_rect = fps_text.get_rect()
                fps_rect.bottomleft = (10, screen.get_height() - 10)
                
                # 敵の統計情報を集計
                enemy_stats = {}
                projectile_stats = {}
                for enemy in enemies:
                    behavior_type = enemy.behavior_type
                    enemy_level = enemy.enemy_type
                    key = f"{behavior_type}-{enemy_level}"
                    enemy_stats[key] = enemy_stats.get(key, 0) + 1
                    
                    # 弾丸の統計も集計
                    projectiles = enemy.get_projectiles()
                    if projectiles:
                        projectile_stats[behavior_type] = projectile_stats.get(behavior_type, 0) + len(projectiles)
                
                # 統計情報のテキストを作成
                stat_lines = []
                behavior_names = {1: "Chase", 2: "Direct", 3: "Shoot", 4: "Turret"}
                for behavior_type in [1, 2, 3, 4]:
                    type_counts = []
                    for level in [1, 2, 3, 4, 5]:
                        key = f"{behavior_type}-{level}"
                        count = enemy_stats.get(key, 0)
                        if count > 0:
                            type_counts.append(f"Lv{level}:{count}")
                    
                    if type_counts:
                        type_name = behavior_names.get(behavior_type, f"Type{behavior_type}")
                        bullets_info = ""
                        if behavior_type in projectile_stats:
                            bullets_info = f" (Bullets:{projectile_stats[behavior_type]})"
                        stat_lines.append(f"{type_name} {' '.join(type_counts)}{bullets_info}")
                
                # アイテム統計も追加
                if len(items) > 0:
                    item_counts = {}
                    for item in items:
                        item_counts[item.type] = item_counts.get(item.type, 0) + 1
                    item_info = " | ".join([f"{k}:{v}" for k, v in item_counts.items()])
                    stat_lines.append(f"Items: {item_info}")
                
                # FPS表示
                bg_rect = fps_rect.inflate(8, 4)
                # 半透明背景用のサーフェス作成
                bg_surf = pygame.Surface((bg_rect.width, bg_rect.height))
                bg_surf.set_alpha(128)
                bg_surf.fill((0, 0, 0))
                screen.blit(bg_surf, bg_rect.topleft)
                screen.blit(fps_text, fps_rect)
                
                # 敵統計表示
                y_offset = fps_rect.top - 5
                for line in stat_lines:
                    if y_offset < 20:  # 画面上部に近づいたら表示を停止
                        break
                    stat_text = fps_font.render(line, True, (255, 255, 255))
                    stat_rect = stat_text.get_rect()
                    stat_rect.bottomleft = (10, y_offset)
                    
                    stat_bg_rect = stat_rect.inflate(8, 4)
                    # 半透明背景用のサーフェス作成
                    stat_bg_surf = pygame.Surface((stat_bg_rect.width, stat_bg_rect.height))
                    stat_bg_surf.set_alpha(128)
                    stat_bg_surf.fill((0, 0, 0))
                    screen.blit(stat_bg_surf, stat_bg_rect.topleft)
                    screen.blit(stat_text, stat_rect)
                    
                    y_offset = stat_rect.top - 5
                
                # パフォーマンス統計の表示（F9でオン/オフ）
                draw_performance_stats(screen, fps_font)
                
                # 全体を一度に更新
                update_rect = pygame.Rect(0, 0, 300, screen.get_height() - y_offset + 20)

            # 描画処理の終了時間を記録（高精度）
            render_end_time = time.perf_counter()
            performance_stats['render_time'] = (render_end_time - render_start_time) * 1000  # ミリ秒に変換

            pygame.display.flip()
            
            # フレーム時間を記録（高精度）
            frame_end_time = time.perf_counter()
            performance_stats['frame_time'] = (frame_end_time - frame_start_time) * 1000  # ミリ秒に変換
            
            # パフォーマンスログの記録（1秒間隔）
            current_time = time.time()
            if performance_logger.should_log(current_time):
                try:
                    # FPSデータの準備
                    current_fps = clock.get_fps() if hasattr(clock, 'get_fps') else 0
                    avg_fps = sum(fps_values[-10:]) / len(fps_values[-10:]) if fps_values else current_fps
                    
                    fps_data = {
                        'fps': avg_fps,
                        'current_fps': current_fps
                    }
                    
                    # ゲームデータの準備
                    game_data = {
                        'game_time': game_time,
                        'frame_count': frame_count
                    }
                    
                    # ログに記録
                    performance_logger.log_performance(performance_stats, game_data, fps_data)
                    
                except Exception as e:
                    print(f"[WARNING] Failed to log performance: {e}")
            
            # フレームスキップ対応のフレームレート制御
            if ENABLE_FRAME_SKIP:
                # デルタタイムベースでフレームレートを制御
                target_fps = FPS  # constants.pyからインポートされたFPSを使用
                current_fps = clock.get_fps() if hasattr(clock, 'get_fps') else target_fps
                if current_fps >= MIN_FPS_THRESHOLD:
                    # FPSが十分な場合は通常通り制御（delta_time補間は常に有効）
                    clock.tick(target_fps)
                else:
                    # FPS低下時は描画最適化でフレームレート向上を図る
                    # delta_time補間により、ゲーム進行速度は既に維持されている
                    target_frame_time_ms = 1000.0 / target_fps
                    actual_frame_time = clock.get_time()
                    if actual_frame_time < target_frame_time_ms:
                        # まだ時間に余裕がある場合は少し待機
                        pygame.time.wait(int(target_frame_time_ms - actual_frame_time))
                    clock.tick(max(MIN_FPS_THRESHOLD, target_fps // 2))  # 最低限のフレームレート保証
            else:
                # 従来のフレームレート制御
                clock.tick(target_fps)
            
            # フレームカウンターをインクリメント（最適化処理で使用）
            frame_count += 1
            if frame_count > 1000000:  # オーバーフロー防止
                frame_count = 0
            
            # FPS計算と表示の更新（0.5秒ごと）
            if SHOW_FPS:
                current_fps = clock.get_fps()
                if current_fps > 0:
                    fps_values.append(current_fps)
                    # FPS値リストのサイズを制限（最大60個、約2秒分）
                    if len(fps_values) > 60:
                        fps_values = fps_values[-60:]
                fps_update_timer += clock.get_time() / 1000.0
                if fps_update_timer >= 0.5:
                    fps_update_timer = 0.0

        except Exception as e:
            # 例外が発生したら詳細をログ出力してループを抜ける
            import traceback
            print("[ERROR] Exception in main loop:", e)
            traceback.print_exc()
            running = False

    print("[INFO] Exited main loop")
    
    # パフォーマンスログを閉じる
    try:
        performance_logger.close()
        print(f"[INFO] Performance log saved: {performance_logger.log_file}")
        print(performance_logger.get_log_summary())
    except Exception as e:
        print(f"[WARNING] Failed to close performance log: {e}")
    
    pygame.quit()

if __name__ == "__main__":
    main()
    sys.exit(0)