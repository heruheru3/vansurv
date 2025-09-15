#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
enemy_no_list内での敵選択比率をテストするスクリプト
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.enemy_spawn_manager import EnemySpawnManager
from collections import defaultdict

def test_enemy_distribution():
    """enemy_no_list内での敵選択比率をテスト"""
    print("=== enemy_no_list内での敵選択比率テスト ===")
    
    spawn_manager = EnemySpawnManager("../data/enemy_spawn_rules.csv")
    
    if not spawn_manager.use_csv_rules:
        print("CSVルールが利用できません")
        return
    
    # 序盤（10秒）での1000回テスト
    test_time = 10
    test_count = 1000
    
    print(f"\n時間 {test_time}秒で {test_count}回テスト...")
    
    # アクティブルールを確認
    active_rules = spawn_manager.get_active_rules(test_time)
    print(f"アクティブルール数: {len(active_rules)}")
    
    for rule in active_rules:
        print(f"ルール{rule['rule_id']}: {rule['description']}")
        print(f"  敵リスト: {rule['enemy_no_list']}, 重み: {rule['spawn_weight']}")
    
    # 1000回選択テスト
    enemy_counts = defaultdict(int)
    rule_counts = defaultdict(int)
    
    for _ in range(test_count):
        enemy_no, rule = spawn_manager.select_enemy_no(test_time)
        enemy_counts[enemy_no] += 1
        if rule:
            rule_counts[rule['rule_id']] += 1
    
    print(f"\n=== 選択結果（{test_count}回） ===")
    
    # ルール別選択回数
    print("ルール別選択回数:")
    for rule_id, count in sorted(rule_counts.items()):
        percentage = (count / test_count) * 100
        print(f"  ルール{rule_id}: {count}回 ({percentage:.1f}%)")
    
    # 敵別選択回数
    print("\n敵別選択回数:")
    total_enemies = sum(enemy_counts.values())
    for enemy_no, count in sorted(enemy_counts.items()):
        percentage = (count / total_enemies) * 100
        print(f"  敵No.{enemy_no}: {count}回 ({percentage:.1f}%)")
    
    # ルール1の敵（1,2,6,7）の割合分析
    rule1_enemies = [1, 2, 6, 7]
    rule1_total = sum(enemy_counts[eno] for eno in rule1_enemies)
    
    if rule1_total > 0:
        print(f"\nルール1の敵（1,2,6,7）内での割合:")
        for enemy_no in rule1_enemies:
            count = enemy_counts[enemy_no]
            percentage = (count / rule1_total) * 100
            print(f"  敵No.{enemy_no}: {count}/{rule1_total} ({percentage:.1f}%)")
    
    # 理論値との比較
    print(f"\n=== 理論値との比較 ===")
    print("ルール1（重み0.8）: 敵1,2,6,7 → 各々 重み0.8")
    print("ルール2（重み0.2）: 敵3,8 → 各々 重み0.2")
    print("総重み = 0.8×4 + 0.2×2 = 3.6")
    print("理論値:")
    print("  ルール1: 80.0% (0.8×4/3.6)")
    print("  ルール2: 20.0% (0.2×2/3.6)")
    print("  ルール1内では各敵: 25.0% (均等)")

if __name__ == "__main__":
    test_enemy_distribution()