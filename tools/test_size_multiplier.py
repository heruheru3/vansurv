#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
size_multiplierの効果を確認するテストスクリプト
"""

import sys
import os

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.enemy_spawn_manager import EnemySpawnManager

def test_size_multiplier_settings():
    """size_multiplierの設定を確認"""
    print("=== size_multiplier設定確認 ===")
    
    spawn_manager = EnemySpawnManager()
    
    # 各時間帯でのサイズ倍率を確認
    test_times = [5, 15, 25, 50, 80, 130]
    
    for game_time in test_times:
        print(f"\n--- 時間 {game_time}秒 ---")
        active_rules = spawn_manager.get_active_rules(game_time)
        
        if not active_rules:
            print("アクティブなルールなし")
            continue
        
        # 敵選択を5回テスト
        size_multipliers = []
        enemy_selections = []
        
        for i in range(5):
            enemy_no, rule = spawn_manager.select_enemy_no(game_time)
            if rule:
                size_mult = rule['size_multiplier']
                size_multipliers.append(size_mult)
                enemy_selections.append(f"敵{enemy_no}(x{size_mult})")
        
        print(f"選択された敵: {', '.join(enemy_selections)}")
        
        # 設定されているサイズ倍率の一覧
        unique_multipliers = set()
        for rule in active_rules:
            unique_multipliers.add(rule['size_multiplier'])
        
        print(f"この時間帯の可能なサイズ倍率: {sorted(unique_multipliers)}")

def main():
    print("size_multiplier効果確認テスト")
    print("=" * 50)
    
    test_size_multiplier_settings()
    
    print("\n" + "=" * 50)
    print("📝 確認事項:")
    print("1. 時間0-30秒でenemy_no 1がsize_multiplier=10で出現")
    print("2. 時間10-40秒でenemy_no 2,7がsize_multiplier=3で出現")
    print("3. ゲーム内で実際に敵のサイズが変わることを目視確認")
    print("\n💡 テスト方法:")
    print("- ゲームを起動して序盤の敵サイズを確認")
    print("- 通常の敵と比べて明らかに大きな敵が出現するか確認")

if __name__ == "__main__":
    main()