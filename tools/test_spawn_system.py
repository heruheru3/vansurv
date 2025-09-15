#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
エネミー出現ルール外部定義化システムのテストスクリプト
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.enemy_spawn_manager import EnemySpawnManager

def test_spawn_manager():
    """EnemySpawnManagerの基本機能をテスト"""
    print("=== エネミー出現ルール外部定義化システム テスト ===")
    
    # スポーンマネージャーの初期化（toolsディレクトリから実行する場合の相対パス）
    print("\n1. スポーンマネージャーの初期化...")
    spawn_manager = EnemySpawnManager("../data/enemy_spawn_rules.csv")
    
    if spawn_manager.use_csv_rules:
        print(f"✓ CSVルールを正常に読み込みました ({len(spawn_manager.spawn_rules)}個のルール)")
    else:
        print("✗ CSVルールの読み込みに失敗。フォールバック機能を使用します")
        return
    
    # 各時間帯での敵選択テスト
    test_times = [10, 40, 80, 130]
    
    for test_time in test_times:
        print(f"\n2. 時間 {test_time}秒でのテスト...")
        
        # アクティブルールの確認
        active_rules = spawn_manager.get_active_rules(test_time)
        print(f"   アクティブルール数: {len(active_rules)}")
        
        for rule in active_rules:
            print(f"   - ルール{rule['rule_id']}: {rule['description']}")
            print(f"     敵リスト: {rule['enemy_no_list']}, 重み: {rule['spawn_weight']}")
            print(f"     強さ倍率: {rule['strength_multiplier']}, サイズ倍率: {rule['size_multiplier']}")
        
        # 敵選択のテスト（複数回実行）
        print(f"   敵選択テスト（5回実行）:")
        enemy_counts = {}
        for i in range(5):
            enemy_no, rule = spawn_manager.select_enemy_no(test_time)
            strength_mult, size_mult = spawn_manager.get_enemy_modifiers(rule)
            
            if enemy_no not in enemy_counts:
                enemy_counts[enemy_no] = 0
            enemy_counts[enemy_no] += 1
            
            desc = rule['description'] if rule else "フォールバック"
            print(f"     試行{i+1}: 敵No.{enemy_no}, 強さ倍率{strength_mult}, サイズ倍率{size_mult} ({desc})")
        
        print(f"   選択された敵の集計: {enemy_counts}")
    
    # デバッグ情報の確認
    print(f"\n3. デバッグ情報の確認 (120秒時点)...")
    debug_info = spawn_manager.get_debug_info(120)
    print(f"   CSVルール使用: {debug_info['use_csv_rules']}")
    print(f"   総ルール数: {debug_info['total_rules']}")
    print(f"   アクティブルール数: {debug_info['active_rules_count']}")
    
    print("\n=== テスト完了 ===")

if __name__ == "__main__":
    test_spawn_manager()