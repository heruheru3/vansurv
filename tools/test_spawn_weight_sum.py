#!/usr/bin/env python3
"""
spawn_weightの合計が1を超える場合の動作テスト

Pythonのrandom.choices()は重みの合計が1を超えていても正常に動作し、
各要素の選択確率は「その要素の重み / 全重みの合計」となります。
"""

import sys
import os
sys.path.append('..')

import random
from collections import defaultdict
from core.enemy_spawn_manager import EnemySpawnManager

def test_weight_sum_behavior():
    """spawn_weightの合計が1を超える場合の動作テスト"""
    
    print("=== spawn_weight合計が1を超える場合の動作テスト ===\n")
    
    # EnemySpawnManagerを初期化
    spawn_manager = EnemySpawnManager()
    
    # 各時間帯でのspawn_weight合計を計算
    test_times = [0, 15, 25, 50, 85, 150]
    
    for game_time in test_times:
        print(f"--- 時間 {game_time}秒 ---")
        
        active_rules = spawn_manager.get_active_rules(game_time)
        if not active_rules:
            print("アクティブなルールなし\n")
            continue
        
        # 重み合計を計算
        total_weight = 0.0
        candidate_count = 0
        
        print("アクティブルール:")
        for rule in active_rules:
            rule_candidates = len(rule['enemy_no_list'])
            rule_weight = rule['spawn_weight']
            total_rule_weight = rule_weight * rule_candidates
            
            print(f"  Rule {rule['rule_id']}: weight={rule_weight}, enemies={rule_candidates}, total_weight={total_rule_weight}")
            print(f"    → enemies: {rule['enemy_no_list']}")
            
            total_weight += total_rule_weight
            candidate_count += rule_candidates
        
        print(f"\n重み合計: {total_weight:.2f}")
        print(f"候補数: {candidate_count}")
        print(f"重み合計が1を{'超過' if total_weight > 1.0 else '以下'}")
        
        # 実際の選択確率をシミュレーション
        print("\n選択確率シミュレーション (10000回試行):")
        selection_count = defaultdict(int)
        num_trials = 10000
        
        for _ in range(num_trials):
            enemy_no, rule = spawn_manager.select_enemy_no(game_time)
            selection_count[enemy_no] += 1
        
        # 結果を表示（選択回数順にソート）
        sorted_results = sorted(selection_count.items(), key=lambda x: x[1], reverse=True)
        
        for enemy_no, count in sorted_results:
            probability = count / num_trials
            print(f"  Enemy {enemy_no}: {count:4d}回 ({probability:.1%})")
        
        print("\n" + "="*50 + "\n")

def test_manual_weight_examples():
    """手動でrandom.choices()の重み動作を確認"""
    
    print("=== manual random.choices() 重み動作確認 ===\n")
    
    test_cases = [
        {
            'name': '重み合計 = 1.0',
            'choices': ['A', 'B', 'C'],
            'weights': [0.5, 0.3, 0.2]
        },
        {
            'name': '重み合計 = 2.0',
            'choices': ['A', 'B', 'C'],
            'weights': [1.0, 0.6, 0.4]
        },
        {
            'name': '重み合計 = 0.5',
            'choices': ['A', 'B', 'C'],
            'weights': [0.25, 0.15, 0.1]
        },
        {
            'name': '重み合計 = 10.0',
            'choices': ['A', 'B', 'C'],
            'weights': [5.0, 3.0, 2.0]
        }
    ]
    
    for case in test_cases:
        print(f"--- {case['name']} ---")
        choices = case['choices']
        weights = case['weights']
        weight_sum = sum(weights)
        
        print(f"選択肢: {choices}")
        print(f"重み: {weights}")
        print(f"重み合計: {weight_sum}")
        
        # 理論確率
        print("理論確率:")
        for i, choice in enumerate(choices):
            theoretical_prob = weights[i] / weight_sum
            print(f"  {choice}: {theoretical_prob:.1%}")
        
        # 実測確率
        print("実測確率 (10000回試行):")
        results = defaultdict(int)
        num_trials = 10000
        
        for _ in range(num_trials):
            selected = random.choices(choices, weights=weights)[0]
            results[selected] += 1
        
        for choice in choices:
            count = results[choice]
            measured_prob = count / num_trials
            print(f"  {choice}: {count:4d}回 ({measured_prob:.1%})")
        
        print()

def main():
    """メイン関数"""
    print("spawn_weight合計が1を超える場合の動作分析\n")
    
    print("重要な仕組み:")
    print("- Python の random.choices() は重みの合計に関係なく動作します")
    print("- 各要素の選択確率 = その要素の重み / 全重みの合計")
    print("- 重みが [0.8, 0.2, 0.8, 0.2] の場合:")
    print("  - 合計 = 2.0")
    print("  - 各要素の確率 = [0.4, 0.1, 0.4, 0.1] (40%, 10%, 40%, 10%)")
    print("- つまり、重み合計が1を超えても正規化されて正常に動作します\n")
    
    test_manual_weight_examples()
    test_weight_sum_behavior()
    
    print("=== 結論 ===")
    print("spawn_weightの合計が1を超えても問題ありません。")
    print("Pythonのrandom.choices()が自動的に正規化して適切な確率で選択します。")
    print("重みの比率が重要で、絶対値は関係ありません。")

if __name__ == "__main__":
    main()