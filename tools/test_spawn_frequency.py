#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
spawn_frequency倍率の動作をテストするスクリプト
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.enemy_spawn_manager import EnemySpawnManager

def test_spawn_frequency():
    """spawn_frequency倍率の動作をテスト"""
    print("=== spawn_frequency倍率テスト ===")
    
    spawn_manager = EnemySpawnManager("../data/enemy_spawn_rules.csv")
    
    if not spawn_manager.use_csv_rules:
        print("CSVルールが利用できません")
        return
    
    # 各時間帯での平均spawn_frequency倍率をテスト
    test_times = [10, 40, 80, 130]
    
    for test_time in test_times:
        print(f"\n=== 時間 {test_time}秒での分析 ===")
        
        # アクティブルールを確認
        active_rules = spawn_manager.get_active_rules(test_time)
        print(f"アクティブルール数: {len(active_rules)}")
        
        # 各ルールの詳細表示
        total_weight = 0.0
        total_weighted_frequency = 0.0
        
        for rule in active_rules:
            rule_weight = rule['spawn_weight'] * len(rule['enemy_no_list'])
            weighted_frequency = rule['spawn_frequency'] * rule_weight
            
            total_weight += rule_weight
            total_weighted_frequency += weighted_frequency
            
            print(f"  ルール{rule['rule_id']}: {rule['description']}")
            print(f"    敵数: {len(rule['enemy_no_list'])}, spawn_weight: {rule['spawn_weight']}, spawn_frequency: {rule['spawn_frequency']}")
            print(f"    実効重み: {rule_weight:.2f}, 重み付き頻度: {weighted_frequency:.2f}")
        
        # 平均spawn_frequency倍率を計算
        avg_frequency = spawn_manager.get_average_spawn_frequency(test_time)
        calculated_avg = total_weighted_frequency / total_weight if total_weight > 0 else 1.0
        
        print(f"\n  計算結果:")
        print(f"    総重み: {total_weight:.2f}")
        print(f"    総重み付き頻度: {total_weighted_frequency:.2f}")
        print(f"    平均spawn_frequency: {avg_frequency:.2f} (計算値: {calculated_avg:.2f})")
        
        # 実際の効果を説明
        if avg_frequency > 1.0:
            effect = f"{avg_frequency:.1f}倍速く敵が出現"
        elif avg_frequency < 1.0:
            effect = f"{1/avg_frequency:.1f}倍遅く敵が出現"
        else:
            effect = "標準的な出現頻度"
        
        print(f"    効果: {effect}")
    
    print(f"\n=== spawn_frequency値の説明 ===")
    print("1.0 = 標準的な出現頻度")
    print("2.0 = 2倍速く出現（スポーンタイマーが2倍速で増加）")
    print("0.5 = 半分の頻度で出現（スポーンタイマーが半分の速度で増加）")
    print("5.0 = 5倍速く出現（序盤のルール1で設定）")

def test_spawn_simulation():
    """スポーン頻度のシミュレーション"""
    print(f"\n=== スポーンタイミングシミュレーション ===")
    
    spawn_manager = EnemySpawnManager("../data/enemy_spawn_rules.csv")
    spawn_interval = 60  # 標準的なスポーン間隔（フレーム）
    
    # 異なる時間帯でのシミュレーション
    test_scenarios = [
        (10, 300),   # 10秒、300フレーム
        (40, 300),   # 40秒、300フレーム  
        (80, 300),   # 80秒、300フレーム
        (130, 300),  # 130秒、300フレーム
    ]
    
    for game_time, total_frames in test_scenarios:
        print(f"\n時間 {game_time}秒でのシミュレーション ({total_frames}フレーム):")
        
        frequency_multiplier = spawn_manager.get_average_spawn_frequency(game_time)
        spawn_timer = 0.0
        spawn_count = 0
        
        for frame in range(total_frames):
            spawn_timer += frequency_multiplier
            if spawn_timer >= spawn_interval:
                spawn_count += 1
                spawn_timer = 0.0
        
        # 標準との比較
        standard_spawns = total_frames // spawn_interval
        
        print(f"  spawn_frequency倍率: {frequency_multiplier:.2f}")
        print(f"  実際のスポーン回数: {spawn_count}回")
        print(f"  標準スポーン回数: {standard_spawns}回")
        print(f"  頻度比: {spawn_count/standard_spawns:.2f}倍" if standard_spawns > 0 else "  頻度比: N/A")

if __name__ == "__main__":
    test_spawn_frequency()
    test_spawn_simulation()