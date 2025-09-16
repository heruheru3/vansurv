#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
レザルト画面表示テストツール

このツールはレザルト画面のみを表示して、レイアウトやボス撃破表示の確認を行います。
ESCキーで終了、SPACEキーでテストデータの切り替えが可能です。
"""

import pygame
import sys
import os

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from constants import *
from ui.ui import draw_ui, draw_end_buttons, get_end_button_rects
from systems.resources import load_icons

def create_test_player():
    """テスト用のプレイヤーオブジェクトを作成"""
    class TestPlayer:
        def __init__(self):
            self.hp = 80
            self.max_hp = 100
            self.exp = 150
            self.level = 5
            self.weapons = {
                "magic_wand": TestWeapon("magic_wand", 3),
                "fire_ball": TestWeapon("fire_ball", 2),
                "ice_lance": TestWeapon("ice_lance", 4),
                "lightning": TestWeapon("lightning", 1),
            }
        
        def get_max_hp(self):
            return self.max_hp
    
    class TestWeapon:
        def __init__(self, name, level):
            self.name = name
            self.level = level
    
    return TestPlayer()

def create_test_damage_stats():
    """テスト用の武器ダメージ統計を作成"""
    return {
        "magic_wand": 15420,
        "fire_ball": 8730,
        "ice_lance": 12350,
        "lightning": 5670,
        "poison_dart": 3240,
        "wind_blade": 7890,
    }

def create_test_enemy_kill_stats():
    """テスト用のエネミー撃破統計を作成"""
    return {
        1: 45,   # スライム
        2: 38,   # ゴブリン
        3: 22,   # オーク
        4: 15,   # トロール
        5: 28,   # スケルトン
        6: 19,   # ゾンビ
        7: 12,   # ワイバーン
        8: 8,    # ドラゴン
        9: 25,   # ウィッチ
        10: 16,  # デーモン
        11: 6,   # エルダードラゴン
        12: 9,   # フェニックス
        13: 14,  # バンパイア
        14: 7,   # リッチ
        15: 4,   # ベヒーモス
        16: 3,   # クラーケン
        17: 11,  # ミノタウロス
        18: 5,   # ハイドラ
        19: 2,   # タイタン
        20: 1,   # エンシェント
    }

def create_test_boss_kill_stats(pattern=1):
    """テスト用のボス撃破統計を作成"""
    if pattern == 1:
        # パターン1: ボス1のみ撃破
        return {1: 1}
    elif pattern == 2:
        # パターン2: 複数ボス撃破
        return {1: 1, 2: 1, 3: 1}
    elif pattern == 3:
        # パターン3: ボス未撃破
        return {}
    elif pattern == 4:
        # パターン4: 全ボス撃破
        return {1: 1, 2: 1, 3: 1, 4: 1, 5: 1}
    elif pattern == 5:
        # パターン5: 単体ボス撃破（ボス3のみ）
        return {3: 1}
    else:
        # パターン6: 複数回撃破（複数カウント）
        return {1: 2, 2: 1, 4: 3}

def main():
    """メイン関数"""
    pygame.init()
    
    # 画面設定
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Result Screen Test Tool")
    clock = pygame.time.Clock()
    
    # アイコン読み込み
    try:
        icons = load_icons()
    except Exception as e:
        print(f"Warning: Could not load icons: {e}")
        icons = {}
    
    # テストデータ
    player = create_test_player()
    damage_stats = create_test_damage_stats()
    enemy_kill_stats = create_test_enemy_kill_stats()
    
    # テストパターン
    test_pattern = 1
    max_patterns = 6  # パターン数を増加
    
    # ゲーム状態
    game_clear = True  # ゲームクリア画面を表示
    game_over = False
    game_time = 300.5  # 5分半のサバイバルタイム
    
    running = True
    print("=== Result Screen Test Tool ===")
    print("Controls:")
    print("  SPACE: Switch test pattern (6 patterns)")
    print("  C: Toggle Clear/Over mode")
    print("  D: Toggle damage stats display")
    print("  LEFT/RIGHT: Select button")
    print("  ENTER: Press button (test mode)")
    print("  ESC: Exit")
    print("")
    print("Test Patterns:")
    print("  1: Boss 1 only defeated")
    print("  2: Multiple bosses defeated (1,2,3)")
    print("  3: No bosses defeated")
    print("  4: All bosses defeated (1-5)")
    print("  5: Boss 3 only defeated")
    print("  6: Multiple defeats (Boss 1×2, Boss 2×1, Boss 4×3)")
    print(f"Current pattern: {test_pattern}")
    
    show_damage_stats = True
    button_selection = 0  # ボタン選択状態（0=Restart, 1=Exit）
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    # テストパターン切り替え
                    test_pattern = (test_pattern % max_patterns) + 1
                    pattern_names = [
                        "Boss 1 only",
                        "Bosses 1,2,3",
                        "No bosses",
                        "All bosses",
                        "Boss 3 only",
                        "Multiple defeats"
                    ]
                    print(f"Switched to pattern {test_pattern}: {pattern_names[test_pattern-1]}")
                elif event.key == pygame.K_c:
                    # クリア/オーバー切り替え
                    game_clear = not game_clear
                    game_over = not game_over
                    mode = "CLEAR" if game_clear else "OVER"
                    print(f"Switched to GAME {mode} mode")
                elif event.key == pygame.K_d:
                    # ダメージ統計表示切り替え
                    show_damage_stats = not show_damage_stats
                    print(f"Damage stats display: {'ON' if show_damage_stats else 'OFF'}")
                elif event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                    # ボタン選択切り替え
                    button_selection = 1 - button_selection
                    button_names = ["Restart", "Exit"]
                    print(f"Button selected: {button_names[button_selection]}")
                elif event.key == pygame.K_RETURN:
                    # ボタン実行（テストなので何もしない）
                    button_names = ["Restart", "Exit"]
                    print(f"Button pressed: {button_names[button_selection]} (Test mode - no action)")
        
        # 背景をクリア
        screen.fill((30, 30, 30))  # ダークグレー背景
        
        # テストパターンに応じてボス撃破統計を更新
        boss_kill_stats = create_test_boss_kill_stats(test_pattern)
        
        # レザルト画面を描画
        try:
            draw_ui(
                screen=screen,
                player=player,
                game_time=game_time,
                game_over=game_over,
                game_clear=game_clear,
                damage_stats=damage_stats if show_damage_stats else None,
                icons=icons,
                show_status=False,  # HPバーなどは非表示
                money=0,
                game_money=1500,
                enemy_kill_stats=enemy_kill_stats,
                boss_kill_stats=boss_kill_stats,
                force_ended=False
            )
            
            # エンドボタンを描画
            draw_end_buttons(screen, game_over, game_clear, button_selection)
            
            # テストパターン情報を画面に表示
            font = pygame.font.Font(None, 24)
            pattern_text = font.render(f"Pattern: {test_pattern}", True, (255, 255, 255))
            mode_text = font.render(f"Mode: {'CLEAR' if game_clear else 'OVER'}", True, (255, 255, 255))
            damage_text = font.render(f"Damage Stats: {'ON' if show_damage_stats else 'OFF'}", True, (255, 255, 255))
            
            screen.blit(pattern_text, (10, 10))
            screen.blit(mode_text, (10, 35))
            screen.blit(damage_text, (10, 60))
            
            # 操作説明
            help_font = pygame.font.Font(None, 20)
            help_texts = [
                "SPACE: Switch pattern",
                "C: Clear/Over mode",
                "D: Toggle damage stats",
                "LEFT/RIGHT: Select button",
                "ENTER: Press button",
                "ESC: Exit"
            ]
            for i, text in enumerate(help_texts):
                help_surface = help_font.render(text, True, (200, 200, 200))
                screen.blit(help_surface, (SCREEN_WIDTH - 200, 10 + i * 22))
                
        except Exception as e:
            # エラーが発生した場合の表示
            error_font = pygame.font.Font(None, 36)
            error_text = error_font.render(f"Error: {str(e)}", True, (255, 100, 100))
            screen.blit(error_text, (50, SCREEN_HEIGHT // 2))
            print(f"Error in draw_ui: {e}")
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    print("Test tool closed.")

if __name__ == "__main__":
    main()