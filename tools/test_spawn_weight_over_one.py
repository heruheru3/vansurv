#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
spawn_weightの合計が1を超える場合の動作テスト

Pythonのrandom.choices()の動作確認：
- 重みの合計が1を超える場合の動作
- 実際の選択確率の計算と確認
"""

import sys
import os
import random
from collections import Counter

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.enemy_spawn_manager import EnemySpawnManager

def test_weight_normalization():
    """重みの正規化動作をテスト"""
    print("=== 重みの正規化動作テスト ===")
    
    # テストケース1: 合計が1
    weights_1 = [0.3, 0.4, 0.3]
    choices_1 = ['A', 'B', 'C']
    
    # テストケース2: 合計が1を超過
    weights_over = [0.8, 0.6, 0.4]  # 合計1.8
    choices_over = ['A', 'B', 'C']
    
    # テストケース3: 合計が1未満
    weights_under = [0.2, 0.2, 0.1]  # 合計0.5
    choices_under = ['A', 'B', 'C']
    
    test_count = 10000
    
    for name, weights, choices in [
        ("合計=1.0", weights_1, choices_1),
        ("合計=1.8", weights_over, choices_over),
        ("合計=0.5", weights_under, choices_under)
    ]:
        print(f"\n--- {name} ---")
        print(f"重み: {weights}")
        print(f"重み合計: {sum(weights)}")
        
        # 実際の選択を実行
        results = Counter()
        for _ in range(test_count):
            selected = random.choices(choices, weights=weights)[0]
            results[selected] += 1
        
        # 理論的確率（正規化後）
        total_weight = sum(weights)
        theoretical_probs = [w / total_weight for w in weights]
        
        print(f"理論的確率: {[f'{p:.3f}' for p in theoretical_probs]}")
        print("実際の結果:")
        for i, choice in enumerate(choices):
            actual_prob = results[choice] / test_count
            theoretical_prob = theoretical_probs[i]
            diff = abs(actual_prob - theoretical_prob)
            print(f"  {choice}: {actual_prob:.3f} (理論値: {theoretical_prob:.3f}, 差: {diff:.3f})")

def analyze_spawn_rules_weights():
    """実際のスポーンルールの重み分析"""
    print("\n\n=== 実際のスポーンルールの重み分析 ===")
    
    spawn_manager = EnemySpawnManager()
    
    # 各時間帯での重み合計を確認
    test_times = [15, 25, 50, 85, 150]
    
    for game_time in test_times:
        print(f"\n--- 時間 {game_time} ---")
        active_rules = spawn_manager.get_active_rules(game_time)
        
        if not active_rules:
            print("アクティブなルールなし")
            continue
        
        print(f"アクティブルール数: {len(active_rules)}")
        
        # 候補と重みを収集（実際のselect_enemy_noロジックと同じ）
        candidates = []
        weights = []
        
        for rule in active_rules:
            for enemy_no in rule['enemy_no_list']:
                candidates.append({
                    'enemy_no': enemy_no,
                    'rule_id': rule['rule_id'],
                    'description': rule['description']
                })
                weights.append(rule['spawn_weight'])
        
        print(f"候補数: {len(candidates)}")
        print(f"重み合計: {sum(weights):.2f}")
        
        # 重み詳細
        weight_groups = {}
        for i, candidate in enumerate(candidates):
            rule_id = candidate['rule_id']
            if rule_id not in weight_groups:
                weight_groups[rule_id] = {
                    'weight': weights[i],
                    'enemies': [],
                    'description': candidate['description']
                }
            weight_groups[rule_id]['enemies'].append(candidate['enemy_no'])
        
        print("ルール別重み:")
        for rule_id, info in weight_groups.items():
            normalized_weight = info['weight'] / sum(weights)
            print(f"  ルール{rule_id}: {info['weight']:.2f} -> {normalized_weight:.3f} "
                  f"(敵: {info['enemies']}, {info['description']})")

def test_actual_enemy_selection():
    """実際の敵選択をテスト"""
    print("\n\n=== 実際の敵選択テスト ===")
    
    spawn_manager = EnemySpawnManager()
    
    # 重みが1を超える時間帯でテスト
    game_time = 25  # 時間10-40の複数ルールが重複
    test_count = 1000
    
    print(f"時間 {game_time} で {test_count} 回選択テスト")
    
    results = Counter()
    rule_usage = Counter()
    
    for _ in range(test_count):
        enemy_no, rule = spawn_manager.select_enemy_no(game_time)
        results[enemy_no] += 1
        if rule:
            rule_usage[rule['rule_id']] += 1
    
    print("\n敵選択結果:")
    for enemy_no, count in sorted(results.items()):
        probability = count / test_count
        print(f"  敵 {enemy_no}: {count}回 ({probability:.3f})")
    
    print("\nルール使用回数:")
    for rule_id, count in sorted(rule_usage.items()):
        probability = count / test_count
        print(f"  ルール {rule_id}: {count}回 ({probability:.3f})")

def main():
    print("spawn_weight合計が1を超える場合の動作テスト")
    print("=" * 60)
    
    # Python random.choices() の基本動作確認
    test_weight_normalization()
    
    # 実際のスポーンルール分析
    analyze_spawn_rules_weights()
    
    # 実際の敵選択テスト
    test_actual_enemy_selection()
    
    print("\n" + "=" * 60)
    print("結論:")
    print("1. random.choices()は重みを自動的に正規化します")
    print("2. 重みの合計が1を超えても、比率は保たれます")
    print("3. 重み0.8の選択肢は重み0.2の選択肢より4倍選ばれやすくなります")
    print("4. 合計値に関係なく、重みの比率が選択確率を決定します")

if __name__ == "__main__":
    main()