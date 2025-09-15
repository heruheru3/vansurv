#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
spawn_frequencyの単位と1秒あたりの出現数を詳細分析するスクリプト
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.enemy_spawn_manager import EnemySpawnManager

def analyze_spawn_frequency_unit():
    """spawn_frequencyの単位と出現数を詳細分析"""
    print("=== spawn_frequency単位・出現数分析 ===")
    
    # 基本パラメータ
    FPS = 60  # フレーム毎秒
    SPAWN_INTERVAL = 60  # フレーム（初期値）
    
    print(f"基本設定:")
    print(f"  FPS: {FPS}")
    print(f"  SPAWN_INTERVAL: {SPAWN_INTERVAL}フレーム")
    print(f"  標準スポーン間隔: {SPAWN_INTERVAL/FPS:.2f}秒")
    
    spawn_manager = EnemySpawnManager("../data/enemy_spawn_rules.csv")
    
    if not spawn_manager.use_csv_rules:
        print("CSVルールが利用できません")
        return
    
    print(f"\n=== spawn_frequencyの仕組み ===")
    print("メインループ:")
    print("  spawn_timer += spawn_frequency  # 毎フレーム実行")
    print("  if spawn_timer >= SPAWN_INTERVAL:")
    print("    # 敵を生成")
    print("    spawn_timer = 0")
    
    print(f"\n=== spawn_frequency=1.0の場合 ===")
    spawn_freq_1 = 1.0
    frames_to_spawn = SPAWN_INTERVAL / spawn_freq_1
    time_to_spawn = frames_to_spawn / FPS
    spawns_per_second = 1 / time_to_spawn
    
    print(f"spawn_frequency = {spawn_freq_1}")
    print(f"スポーンまでのフレーム数: {frames_to_spawn:.1f}フレーム")
    print(f"スポーン間隔: {time_to_spawn:.2f}秒")
    print(f"1秒あたりの出現回数: {spawns_per_second:.3f}回")
    
    # 各時間帯での実際の出現数計算
    test_times = [10, 40, 80, 130]
    
    for game_time in test_times:
        print(f"\n=== 時間 {game_time}秒での分析 ===")
        
        frequency_multiplier = spawn_manager.get_average_spawn_frequency(game_time)
        
        # スポーン間隔の計算
        effective_frames_to_spawn = SPAWN_INTERVAL / frequency_multiplier
        effective_time_to_spawn = effective_frames_to_spawn / FPS
        effective_spawns_per_second = 1 / effective_time_to_spawn
        
        print(f"平均spawn_frequency: {frequency_multiplier:.2f}")
        print(f"実効スポーン間隔: {effective_time_to_spawn:.2f}秒")
        print(f"1秒あたりの出現回数: {effective_spawns_per_second:.3f}回")
        
        # 1回のスポーンで生成される敵数も考慮
        # 簡略化：時間に応じた num_enemies の計算
        if game_time <= 30:
            num_enemies = 1 + int(game_time // 10)
        else:
            base_enemies = 1 + int((game_time - 30) // 20)
            num_enemies = base_enemies + int((game_time ** 1.2) / 15)
        
        num_enemies = min(num_enemies, 8)
        
        total_enemies_per_second = effective_spawns_per_second * num_enemies
        
        print(f"1回のスポーンでの敵数: {num_enemies}体")
        print(f"1秒あたりの総敵出現数: {total_enemies_per_second:.2f}体")

def test_different_spawn_frequencies():
    """異なるspawn_frequency値での出現パターンテスト"""
    print(f"\n=== 異なるspawn_frequency値でのテスト ===")
    
    FPS = 60
    SPAWN_INTERVAL = 60
    
    test_frequencies = [0.3, 0.5, 1.0, 1.5, 2.0, 5.0]
    
    print("| spawn_frequency | スポーン間隔(秒) | 1秒あたり出現回数 | 効果 |")
    print("|----------------|-----------------|------------------|------|")
    
    for freq in test_frequencies:
        frames_to_spawn = SPAWN_INTERVAL / freq
        time_to_spawn = frames_to_spawn / FPS
        spawns_per_second = 1 / time_to_spawn
        
        if freq < 1.0:
            effect = f"{1/freq:.1f}倍遅い"
        elif freq > 1.0:
            effect = f"{freq:.1f}倍速い"
        else:
            effect = "標準"
        
        print(f"| {freq:13.1f} | {time_to_spawn:13.2f} | {spawns_per_second:14.3f} | {effect:4s} |")

def simulate_1_second_spawning():
    """1秒間のスポーニングシミュレーション"""
    print(f"\n=== 1秒間のスポーニングシミュレーション ===")
    
    spawn_manager = EnemySpawnManager("../data/enemy_spawn_rules.csv")
    FPS = 60
    SPAWN_INTERVAL = 60
    
    test_scenarios = [
        (10, 1.0),   # 標準的なspawn_frequency
        (10, 5.0),   # 実際のCSV設定（序盤）
        (40, 0.96),  # 実際のCSV設定（中盤）
    ]
    
    for game_time, manual_freq in test_scenarios:
        actual_freq = spawn_manager.get_average_spawn_frequency(game_time)
        print(f"\n時間 {game_time}秒 (実際のCSV頻度: {actual_freq:.2f}):")
        
        spawn_timer = 0.0
        spawn_count = 0
        
        for frame in range(FPS):  # 1秒 = 60フレーム
            spawn_timer += actual_freq
            if spawn_timer >= SPAWN_INTERVAL:
                spawn_count += 1
                spawn_timer = 0.0
        
        print(f"  1秒間のスポーン回数: {spawn_count}回")
        
        # 敵数計算
        if game_time <= 30:
            num_enemies = 1 + int(game_time // 10)
        else:
            base_enemies = 1 + int((game_time - 30) // 20)
            num_enemies = base_enemies + int((game_time ** 1.2) / 15)
        num_enemies = min(num_enemies, 8)
        
        total_enemies = spawn_count * num_enemies
        print(f"  1回あたりの敵数: {num_enemies}体")
        print(f"  1秒間の総敵数: {total_enemies}体")

if __name__ == "__main__":
    analyze_spawn_frequency_unit()
    test_different_spawn_frequencies()
    simulate_1_second_spawning()