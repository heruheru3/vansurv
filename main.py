import pygame
import sys
import math
import random
import os
from constants import *

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

from player import Player
from enemy import Enemy
from effects.items import ExperienceGem, GameItem, MoneyItem
from effects.particles import DeathParticle, PlayerHurtParticle, HurtFlash, LevelUpEffect, SpawnParticle, DamageNumber, AvoidanceParticle, HealEffect, AutoHealEffect
from ui import draw_ui, draw_minimap, draw_level_choice, draw_end_buttons, get_end_button_rects
from stage import draw_stage_background
from box import BoxManager  # アイテムボックス管理用
import stage
import resources
from game_utils import init_game_state, limit_particles, enforce_experience_gems_limit
from game_logic import (spawn_enemies, handle_enemy_death, handle_bomb_item_effect, 
                       update_difficulty, handle_player_level_up, collect_experience_gems, collect_items)
from collision import check_player_enemy_collision, check_attack_enemy_collision
from map import MapLoader
from save_system import SaveSystem

# ランタイムで切り替え可能なデバッグフラグ（F3でトグル）
DEBUG_MODE = DEBUG


def main():
    global DEBUG_MODE
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
        from audio import audio
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
        from enemy import Enemy
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

    # パーティクルの並列update関数（制限付き）
    def parallel_update_particles(particles):
        # パーティクル数制限でパフォーマンス向上
        max_particles = 200  # 最大パーティクル数
        if len(particles) > max_particles:
            # 古いパーティクルを削除（新しいものを優先）
            particles = particles[-max_particles:]
        
        # シンプル化: スレッドプールは毎フレーム作ると重いので逐次実行に戻す（多くのケースで高速）
        new_particles = []
        for p in particles:
            try:
                if p.update():
                    new_particles.append(p)
            except Exception:
                pass
        return new_particles

    # お金関連の初期化
    current_game_money = 0  # 現在のゲームセッションで獲得したお金
    enemies_killed_this_game = 0  # 今回のゲームで倒した敵の数
    
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
            print(f"[INFO] Creating sample CSV map: {csv_path}")
            map_loader.create_sample_csv(csv_path)
            
        # マップを読み込み（PyInstallerの場合はリソースから）
        success = map_loader.load_csv_map(csv_path)
        if not success:
            print("[WARNING] Failed to load CSV map, using default map")
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
            from audio import audio
            audio.play_sound('heal', duration=0.5, fade_out=0.1)
        except Exception:
            pass
    
    player.heal_effect_callback = heal_effect_callback

    # デバッグ: 初期状態の選択フラグ確認
    try:
        print(f"[DEBUG] initial awaiting_weapon_choice={getattr(player,'awaiting_weapon_choice', False)} last_level_choices={getattr(player,'last_level_choices', [])}")
    except Exception:
        pass

    # メインゲームループ
    running = True
    frame_count = 0  # フレームカウンターを初期化
    print("[INFO] Entering main loop")
    while running:
        try:
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

                    # ESCキーでゲーム途中でも強制終了
                    if event.key == pygame.K_ESCAPE and not game_over and not game_clear:
                        print("[INFO] Game forcibly ended by ESC key")
                        # 強制終了フラグを立てる（game_overと同じ扱い）
                        game_over = True
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

                    if event.key == pygame.K_RETURN and (game_over or game_clear):
                        # ゲームクリア後は（規定時間生存）プレイヤー状態を保持して続行する
                        if game_clear:
                            print("[INFO] Survived required time - continuing without resetting player/weapons.")
                            # ゲームクリアボーナスを追加
                            current_game_money += MONEY_GAME_CLEAR_BONUS
                            # セーブデータに記録（クリアボーナス含む）
                            save_system.add_money(current_game_money + int(game_time * MONEY_PER_SURVIVAL_SECOND))
                            save_system.record_game_end(game_time, player.level, enemies_killed_this_game, player.exp)
                            # 武器使用統計も記録
                            if damage_stats:
                                save_system.record_weapon_usage(damage_stats)
                            # 実績チェック
                            save_system.check_achievements()
                            save_system.save()
                            print(f"[INFO] Game data saved. Total money now: {save_system.get_money()}G")
                            
                            enemies = []
                            experience_gems = []
                            items = []
                            particles = []
                            spawn_timer = 0
                            boss_spawn_timer = 0  # ボススポーンタイマーもリセット
                            spawn_interval = 60
                            game_time = 0
                            last_difficulty_increase = 0
                            game_clear = False
                            # リセット
                            current_game_money = 0
                            enemies_killed_this_game = 0
                            # ボックスマネージャーをリセット
                            box_manager = BoxManager()
                        else:
                            # 通常のリスタート（全て再初期化）
                            # セーブデータに記録（生存時間ボーナス含む）
                            save_system.add_money(current_game_money + int(game_time * MONEY_PER_SURVIVAL_SECOND))
                            save_system.record_game_end(game_time, player.level, enemies_killed_this_game, player.exp)
                            # 武器使用統計も記録
                            if damage_stats:
                                save_system.record_weapon_usage(damage_stats)
                            # 実績チェック
                            save_system.check_achievements()
                            save_system.save()
                            print(f"[INFO] Game data saved. Total money now: {save_system.get_money()}G")
                            save_system.save()
                            print(f"[INFO] Game data saved. Total money now: {save_system.get_money()}G")
                            
                            player, enemies, experience_gems, items, game_over, game_clear, spawn_timer, spawn_interval, game_time, last_difficulty_increase, particles, damage_stats, boss_spawn_timer, spawned_boss_types = init_game_state(screen, save_system)
                            # リセット
                            current_game_money = 0
                            enemies_killed_this_game = 0
                            # ボックスマネージャーをリセット
                            box_manager = BoxManager()

                        # 武器使用統計も記録
                        if damage_stats:
                            save_system.record_weapon_usage(damage_stats)
                        # 実績チェック
                        save_system.check_achievements()
                        save_system.save()
                        print(f"[INFO] Game data saved (forced end). Total money now: {save_system.get_money()}G")
                    
                    # HP回復エフェクト用のコールバックを設定
                    def heal_effect_callback(x, y, heal_amount, is_auto=False):
                        if is_auto:
                            particles.append(AutoHealEffect(x, y))
                        particles.append(HealEffect(x, y, heal_amount))
                    player.heal_effect_callback = heal_effect_callback
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # マウス座標を仮想画面座標に変換
                    def convert_mouse_pos(mouse_x, mouse_y):
                        # オフセットを引いてからスケールで割る
                        virtual_x = (mouse_x - offset_x) / scale_factor if scale_factor > 0 else mouse_x
                        virtual_y = (mouse_y - offset_y) / scale_factor if scale_factor > 0 else mouse_y
                        # 仮想画面の範囲内にクランプ
                        virtual_x = max(0, min(SCREEN_WIDTH, virtual_x))
                        virtual_y = max(0, min(SCREEN_HEIGHT, virtual_y))
                        return int(virtual_x), int(virtual_y)
                    
                    # マウスで選択可能ならクリック位置を判定
                    if getattr(player, 'awaiting_weapon_choice', False) and event.button == 1:
                        player.set_input_method("mouse")
                        mx, my = convert_mouse_pos(*event.pos)
                        
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
                        mx, my = convert_mouse_pos(*event.pos)
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
                        mx, my = convert_mouse_pos(*event.pos)
                        try:
                            rects = get_end_button_rects()
                            # Continue はゲームオーバー時のみ有効
                            if game_over and rects.get('continue') and rects['continue'].collidepoint(mx, my):
                                player.hp = player.get_max_hp()
                                game_over = False
                                for _ in range(8):
                                    particles.append(DeathParticle(player.x, player.y, CYAN))
                                continue
                            # GAME CLEAR の Continue: 残り時間を規定値に戻して続行
                            if game_clear and rects.get('continue') and rects['continue'].collidepoint(mx, my):
                                try:
                                    # reset game_time to 0 on continue from game clear
                                    game_time = 0
                                except Exception:
                                    game_time = 0
                                game_clear = False
                                # 画面エフェクト
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
                                # リセット
                                current_game_money = 0
                                enemies_killed_this_game = 0
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
                player.move(int(camera_x), int(camera_y), get_virtual_mouse_pos)

                # 自動攻撃の更新（仮想マウス座標も渡す）
                player.update_attacks(enemies, camera_x=int(camera_x), camera_y=int(camera_y), get_virtual_mouse_pos=get_virtual_mouse_pos)

                # 自然回復（HPサブアイテム所持時のみ、2秒で1回復）
                try:
                    player.update_regen()
                except Exception:
                    pass

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
                            from audio import audio
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
                                        from audio import audio
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
                                        from box import ItemBox
                                        special_box = ItemBox(enemy.x, enemy.y, box_type=4)
                                        box_manager.boxes.append(special_box)
                                        # 大きめのスポーンエフェクト
                                        if len(particles) < 300:
                                            for _ in range(12):
                                                particles.append(SpawnParticle(special_box.x, special_box.y, (255, 100, 100)))
                                        print(f"[INFO] Special boss box spawned at ({special_box.x:.0f},{special_box.y:.0f})")
                                    except Exception as e:
                                        print(f"[WARNING] Failed to spawn boss special box: {e}")

                                # 撃破カウンターを増加
                                enemies_killed_this_game += 1
                                current_game_money += MONEY_PER_ENEMY_KILLED

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

                # ゲーム時間の更新（60FPSを想定）
                game_time += 1/60

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
                
                # Noベースでボス設定を処理（重複を避けるため）
                for key, boss_config in all_boss_configs.items():
                    # Noベースのエントリのみを処理（タプルキーは互換性用なのでスキップ）
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
                            
                            # ボスを画面外からスポーン
                            screen_margin = 100  # 画面外の距離
                            side = random.randint(0, 3)  # 0:上, 1:右, 2:下, 3:左
                            
                            if side == 0:  # 上から
                                boss_x = player.x + random.randint(-SCREEN_WIDTH//2, SCREEN_WIDTH//2)
                                boss_y = player.y - SCREEN_HEIGHT//2 - screen_margin
                            elif side == 1:  # 右から
                                boss_x = player.x + SCREEN_WIDTH//2 + screen_margin
                                boss_y = player.y + random.randint(-SCREEN_HEIGHT//2, SCREEN_HEIGHT//2)
                            elif side == 2:  # 下から
                                boss_x = player.x + random.randint(-SCREEN_WIDTH//2, SCREEN_WIDTH//2)
                                boss_y = player.y + SCREEN_HEIGHT//2 + screen_margin
                            else:  # 左から
                                boss_x = player.x - SCREEN_WIDTH//2 - screen_margin
                                boss_y = player.y + random.randint(-SCREEN_HEIGHT//2, SCREEN_HEIGHT//2)
                            
                            # ワールド境界をクランプ
                            boss_x = max(50, min(WORLD_WIDTH - 50, boss_x))
                            boss_y = max(50, min(WORLD_HEIGHT - 50, boss_y))
                            
                            # ボス生成（NoベースでCSVの設定に基づき）
                            boss_stats_key = (boss_type, level, spawn_time)  # 互換性用
                            boss = Enemy(screen, game_time, spawn_x=boss_x, spawn_y=boss_y, is_boss=True, boss_type=boss_type, boss_image_file=boss_config['image_file'], boss_stats_key=boss_stats_key, boss_no=boss_no)
                            enemies.append(boss)
                            
                            # この特定のNoのボスを出現済みリストに追加
                            spawned_boss_types.add(boss_no)
                            
                            # ボススポーンエフェクト（軽量化）
                            if len(particles) < 300:
                                for _ in range(6):  # スパイクを抑える
                                    particles.append(SpawnParticle(boss_x, boss_y, (255, 215, 0)))  # 金色
                            
                            # 現在のボス数をログ出力
                            boss_count = sum(1 for enemy in enemies if getattr(enemy, 'is_boss', False))
                            print(f"[INFO] Boss No.{boss_no} (Type {boss_type}) spawned at ({boss_x:.0f}, {boss_y:.0f}). Player at ({player.x:.0f}, {player.y:.0f}). Total bosses: {boss_count}")

                # 敵の生成を爆発的に
                spawn_timer += 1
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
                        margin = 32
                        side = random.randint(0, 3)
                        if side == 0:
                            sx = random.randint(cam_vx - margin, cam_vx + SCREEN_WIDTH + margin)
                            sy = cam_vy - margin
                        elif side == 1:
                            sx = cam_vx + SCREEN_WIDTH + margin
                            sy = random.randint(cam_vy - margin, cam_vy + SCREEN_HEIGHT + margin)
                        elif side == 2:
                            sx = random.randint(cam_vx - margin, cam_vx + SCREEN_WIDTH + margin)
                            sy = cam_vy + SCREEN_HEIGHT + margin
                        else:
                            sx = cam_vx - margin
                            sy = random.randint(cam_vy - margin, cam_vy + SCREEN_HEIGHT + margin)

                        sx = max(-margin, min(WORLD_WIDTH + margin, sx))
                        sy = max(-margin, min(WORLD_HEIGHT + margin, sy))

                        enemy = Enemy(screen, game_time, spawn_x=sx, spawn_y=sy, spawn_side=side)
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
                        if DEBUG and enemies_to_remove > 0:
                            print(f"[DEBUG] Removing {enemies_to_remove} enemies due to limit (current: {len(regular_enemies)}, max: {MAX_ENEMIES}, bosses: {len(boss_enemies)})")
                        
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
                        # ただし、視界内の敵は絶対に削除しない
                        if removed < enemies_to_remove:
                            if DEBUG:
                                print(f"[DEBUG] WARNING: Could not remove enough enemies without affecting visible enemies ({removed}/{enemies_to_remove})")
                        
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

                # エネミー移動処理（全エネミー動作継続、軽量化は別手法で実現）
                for enemy in enemies[:]:
                    # ノックバック更新処理
                    if hasattr(enemy, 'update_knockback'):
                        enemy.update_knockback()
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

                    enemy.move(player, camera_x=int(camera_x), camera_y=int(camera_y), map_loader=map_loader, enemies=nearby)
                    
                    # ボスの画面外チェックとリスポーン処理
                    if hasattr(enemy, 'is_boss') and enemy.is_boss:
                        if hasattr(enemy, 'is_boss_off_screen') and enemy.is_boss_off_screen():
                            # ボスを画面外からランダムにリスポーン（HPは維持）
                            enemy.respawn_boss_randomly(player)
                            
                            # リスポーンエフェクト
                            if len(particles) < 300:
                                for _ in range(10):
                                    particles.append(SpawnParticle(enemy.x, enemy.y, (255, 215, 0)))  # 金色
                    
                    # 敵の攻撃処理（動作継続、頻度調整で軽量化）
                    # 画面外エネミーの攻撃頻度を調整（完全停止せず、間引きのみ）
                    attack_should_update = True
                    if enemy.is_off_screen():
                        # 画面外は頻度を下げるが完全停止はしない
                        if len(enemies) > 100:
                            attack_should_update = (frame_count % 8 == 0)  # 1/8頻度
                        else:
                            attack_should_update = (frame_count % 4 == 0)  # 1/4頻度
                    
                    if attack_should_update:
                        enemy.update_attack(player)
                        # 弾丸更新は軽量化のため頻度を下げる（ボスは除外）
                        if getattr(enemy, 'is_boss', False) or frame_count % 2 == 0:
                            enemy.update_projectiles(player)

                    # --- 画面外リポップ仕様: ノーマルエネミーがカメラ外（マージン付き）に出たら削除して
                    #     画面外からポップする形で再出現させる（ボスは除外） ---
                    try:
                        if not getattr(enemy, 'is_boss', False):
                            # カメラ境界にマージンを追加して判定（縦横100px）
                            MARGIN = 100
                            cam_left = int(camera_x) - MARGIN
                            cam_right = int(camera_x) + SCREEN_WIDTH + MARGIN
                            cam_top = int(camera_y) - MARGIN
                            cam_bottom = int(camera_y) + SCREEN_HEIGHT + MARGIN

                            if (enemy.x < cam_left or enemy.x > cam_right or
                                enemy.y < cam_top or enemy.y > cam_bottom):
                                # 削除予定に入れる
                                enemies_to_remove.append(enemy)

                                # 画面外（カメラ端の外側）から出現するように生成位置を決定
                                spawn_margin = 100
                                side = random.randint(0, 3)  # 0:上,1:右,2:下,3:左
                                if side == 0:  # 上
                                    sx = random.randint(int(camera_x) - spawn_margin, int(camera_x) + SCREEN_WIDTH + spawn_margin)
                                    sy = int(camera_y) - spawn_margin
                                elif side == 1:  # 右
                                    sx = int(camera_x) + SCREEN_WIDTH + spawn_margin
                                    sy = random.randint(int(camera_y) - spawn_margin, int(camera_y) + SCREEN_HEIGHT + spawn_margin)
                                elif side == 2:  # 下
                                    sx = random.randint(int(camera_x) - spawn_margin, int(camera_x) + SCREEN_WIDTH + spawn_margin)
                                    sy = int(camera_y) + SCREEN_HEIGHT + spawn_margin
                                else:  # 左
                                    sx = int(camera_x) - spawn_margin
                                    sy = random.randint(int(camera_y) - spawn_margin, int(camera_y) + SCREEN_HEIGHT + spawn_margin)

                                # ワールド境界をクランプ
                                sx = max(50, min(WORLD_WIDTH - 50, sx))
                                sy = max(50, min(WORLD_HEIGHT - 50, sy))

                                # 生成は画面外から行うので spawn_x/spawn_y のみ渡す
                                new_enemies_to_add.append(Enemy(screen, game_time, spawn_x=sx, spawn_y=sy))
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
                        if random.random() < player.get_avoidance():
                            # サブアイテムスピードアップ効果で攻撃を回避
                            particles.append(AvoidanceParticle(player.x, player.y))
                            try:
                                from effects.particles import LuckyText
                                particles.append(LuckyText(player.x, player.y - getattr(player, 'size', 32) - 6, "Lukey!", color=CYAN))
                            except Exception:
                                pass
                        else:
                            # 無敵時間チェック
                            now_ms = pygame.time.get_ticks()
                            last_hit = getattr(player, 'last_hit_time', -999999)
                            if now_ms - last_hit >= INVINCIBLE_MS:
                                particles.append(HurtFlash(player.x, player.y, size=player.size))

                                # サブアイテムアーマーの効果でダメージを軽減
                                try:
                                    player.hp -= max(1, int(enemy.damage - player.get_defense()))
                                except Exception:
                                    player.hp -= enemy.damage

                                # 被弾時刻を更新
                                try:
                                    player.last_hit_time = now_ms
                                except Exception:
                                    pass

                                # サウンド: プレイヤー被弾
                                try:
                                    from audio import audio
                                    audio.play_sound('player_hurt')
                                except Exception:
                                    pass

                                # エネミーは削除しない（継続して存在）
                                # if not getattr(enemy, 'is_boss', False):
                                #     enemies.remove(enemy)
                                if player.hp <= 0:
                                    game_over = True
                            else:
                                # 無敵中はノーダメージ、エネミーも削除しない
                                pass
                                # try:
                                #     if not getattr(enemy, 'is_boss', False):
                                #         enemies.remove(enemy)
                                # except Exception:
                                #     pass

                # 敵の弾丸とプレイヤーの衝突判定（負荷軽減）
                # エネミー弾丸処理（効率化：事前計算）
                total_projectiles = sum(len(enemy.get_projectiles()) for enemy in enemies)
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
                                if random.random() < player.get_avoidance():
                                    # 攻撃を回避
                                    particles.append(AvoidanceParticle(player.x, player.y))
                                    try:
                                        from effects.particles import LuckyText
                                        particles.append(LuckyText(player.x, player.y - getattr(player, 'size', 32) - 6, "Dodge!", color=CYAN))
                                    except Exception:
                                        pass
                                else:
                                    # 無敵時間チェック
                                    now_ms = pygame.time.get_ticks()
                                    last_hit = getattr(player, 'last_hit_time', -999999)
                                    if now_ms - last_hit >= INVINCIBLE_MS:
                                        particles.append(HurtFlash(player.x, player.y, size=player.size))

                                        # ダメージを適用
                                        try:
                                            player.hp -= max(1, int(projectile.damage - player.get_defense()))
                                        except Exception:
                                            player.hp -= projectile.damage

                                        # 被弾時刻を更新
                                        try:
                                            player.last_hit_time = now_ms
                                        except Exception:
                                            pass

                                        # サウンド: プレイヤー被弾（弾）
                                        try:
                                            from audio import audio
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
                        from audio import audio
                        # 複数ジェム取得時は音量を少し上げる（最大1.0）
                        volume = min(1.0, 0.6 + gems_collected_this_frame * 0.1)
                        # min_intervalを短めに設定してレスポンスを良くする
                        audio.play_sound('gem_pickup', volume=volume, min_interval=0.1)
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
                            if DEBUG:
                                print(f"[DEBUG] Money collected: {money_amount}G ({money_type})")
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
                particles = parallel_update_particles(particles)

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

            # 仮想画面をクリア
            virtual_screen.fill((0, 0, 0))

            # ワールド用サーフェスに描画してから仮想画面にブリットする
            world_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

            # 背景描画（設定により切り替え）
            if USE_CSV_MAP:
                # CSVマップ背景
                map_loader.draw_map(world_surf, int_cam_x, int_cam_y)
            else:
                # テスト用市松模様背景
                draw_test_checkerboard(world_surf, int_cam_x, int_cam_y)
            
            # 敵の描画（画面内優先、画面外も一部描画）
            screen_margin = 150  # マージンを拡大
            screen_left = int_cam_x - screen_margin
            screen_right = int_cam_x + SCREEN_WIDTH + screen_margin
            screen_top = int_cam_y - screen_margin
            screen_bottom = int_cam_y + SCREEN_HEIGHT + screen_margin
            
            # 画面内エネミーを優先描画、画面外も制限付きで描画
            enemies_drawn = 0
            screen_enemies = []
            offscreen_enemies = []
            
            for enemy in enemies:
                if (enemy.x >= screen_left and enemy.x <= screen_right and 
                    enemy.y >= screen_top and enemy.y <= screen_bottom):
                    screen_enemies.append(enemy)  # 画面内
                else:
                    offscreen_enemies.append(enemy)  # 画面外
            
            # 画面内エネミーは全て描画
            for enemy in screen_enemies:
                enemy.draw(world_surf, int_cam_x, int_cam_y)
                enemy.draw_projectiles(world_surf, int_cam_x, int_cam_y)
            
            # 画面外エネミーも一部描画（完全カットはしない）
            max_offscreen_draw = min(30, len(offscreen_enemies))  # 画面外も30体まで描画
            for enemy in offscreen_enemies[:max_offscreen_draw]:
                enemy.draw(world_surf, int_cam_x, int_cam_y)
                enemy.draw_projectiles(world_surf, int_cam_x, int_cam_y)
            
            # ボックスの描画（敵の後、パーティクルの前）
            box_manager.draw_all(world_surf, int_cam_x, int_cam_y)

            # パーティクル（ワールド座標）の描画（エネミーの後、攻撃エフェクトの前に追加）
            # HurtFlash, LevelUpEffect は画面オーバーレイなので別途画面に描画する
            world_particles = [p for p in particles if not isinstance(p, (HurtFlash, LevelUpEffect))]
            overlay_particles = [p for p in particles if isinstance(p, (HurtFlash, LevelUpEffect))]
            for particle in world_particles:
                # 各パーティクルは world_surf 上に描画する（カメラオフセットを渡す）
                try:
                    particle.draw(world_surf, int_cam_x, int_cam_y)
                except TypeError:
                    # 古いインターフェースのままなら位置をオフセットして描画
                    particle.draw(world_surf)

            # 経験値ジェムの描画
            for gem in experience_gems:
                gem.draw(world_surf, int_cam_x, int_cam_y)

            # アイテムの描画
            for item in items:
                item.draw(world_surf, int_cam_x, int_cam_y)

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

            # デバッグ: ゲーム終了時に damage_stats の中身をログ出力 (表が出ない原因調査用)
            try:
                if (game_over or game_clear) and DEBUG_MODE:
                    if not damage_stats:
                        print("[DEBUG] damage_stats is empty at game end")
                    else:
                        print(f"[DEBUG] damage_stats keys={list(damage_stats.items())[:8]}")
            except Exception:
                pass
            # UI描画を仮想画面に（毎フレーム描画でちらつき防止）
            draw_ui(virtual_screen, player, game_time, game_over, game_clear, damage_stats, ICONS, show_status=show_status, game_money=current_game_money)
            # エンド画面のボタンを描画（描画だけでクリックはイベントハンドラで処理）
            if game_over or game_clear:
                from ui import draw_end_buttons
                draw_end_buttons(virtual_screen, game_over, game_clear)
            
            # レベルアップ候補がある場合はポップアップを ui.draw_level_choice に任せる
            # サブアイテム選択 UI を優先して表示
            if getattr(player, 'awaiting_subitem_choice', False) and getattr(player, 'last_subitem_choices', None):
                # サブアイテム選択は ui.draw_subitem_choice を使う
                from ui import draw_subitem_choice
                draw_subitem_choice(virtual_screen, player, ICONS)
            elif getattr(player, 'awaiting_weapon_choice', False) and getattr(player, 'last_level_choices', None):
                draw_level_choice(virtual_screen, player, ICONS)

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
                
                # 全体を一度に更新
                update_rect = pygame.Rect(0, 0, 300, screen.get_height() - y_offset + 20)

            pygame.display.flip()
            
            # パフォーマンス最適化：大きなスケーリング時はFPSを調整
            target_fps = FULLSCREEN_FPS if scale_factor > FULLSCREEN_FPS_THRESHOLD else NORMAL_FPS
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
    pygame.quit()

if __name__ == "__main__":
    main()
    sys.exit(0)