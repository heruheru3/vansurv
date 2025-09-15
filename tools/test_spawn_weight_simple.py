#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
spawn_weightの合計が1を超える場合の動作テスト（簡易版）

Pythonのrandom.choices()の動作確認のみ
"""

import random
from collections import Counter

def test_weight_normalization():
    """重みの正規化動作をテスト"""
    print("=== 重みの正規化動作テスト ===")
    
    # テストケース1: 合計が1
    weights_1 = [0.3, 0.4, 0.3]
    choices_1 = ['A', 'B', 'C']
    
    # テストケース2: 合計が1を超過（実際のCSVと同じパターン）
    weights_over = [0.8, 0.2, 0.8, 0.2]  # 合計2.0（時間10-40と同じ）
    choices_over = ['Enemy1', 'Enemy6', 'Enemy2', 'Enemy7']
    
    # テストケース3: 合計が1未満
    weights_under = [0.2, 0.2, 0.1]  # 合計0.5
    choices_under = ['A', 'B', 'C']
    
    test_count = 10000
    
    for name, weights, choices in [
        ("合計=1.0", weights_1, choices_1),
        ("合計=2.0（CSVの時間10-40と同様）", weights_over, choices_over),
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
        
        print(f"理論的確率（正規化後）:")
        for i, choice in enumerate(choices):
            print(f"  {choice}: {theoretical_probs[i]:.3f}")
        
        print("実際の結果:")
        for i, choice in enumerate(choices):
            actual_prob = results[choice] / test_count
            theoretical_prob = theoretical_probs[i]
            diff = abs(actual_prob - theoretical_prob)
            print(f"  {choice}: {actual_prob:.3f} (理論値: {theoretical_prob:.3f}, 差: {diff:.3f})")

def analyze_csv_weight_patterns():
    """CSVファイルの重みパターンを分析"""
    print("\n\n=== CSVファイルの重みパターン分析 ===")
    
    # 実際のCSVデータから時間帯別の重み合計を計算
    time_ranges = [
        ("0-30", [0.8, 0.2]),  # ルール1,2
        ("10-40", [0.8, 0.2, 0.8, 0.2]),  # ルール1,2,3,4 → 合計2.0
        ("30-60", [0.5, 0.3, 0.2]),  # ルール5,6,7
        ("70-100", [0.3, 0.25, 0.25, 0.2]),  # ルール8,9,10,11
        ("120以降", [0.2, 0.2, 0.3, 0.25, 0.05])  # ルール12,13,14,15,16
    ]
    
    for time_range, weights in time_ranges:
        total = sum(weights)
        print(f"\n時間帯 {time_range}:")
        print(f"  重み: {weights}")
        print(f"  合計: {total}")
        if total > 1.0:
            print(f"  ⚠️  合計が1を超過（{total:.1f}倍）")
            print(f"  正規化後の重み: {[w/total for w in weights]}")
        elif total < 1.0:
            print(f"  ℹ️  合計が1未満（{total:.1f}）")
            print(f"  正規化後の重み: {[w/total for w in weights]}")
        else:
            print(f"  ✓ 合計がちょうど1.0")

def demonstrate_ratio_preservation():
    """重みの比率保持を実証"""
    print("\n\n=== 重みの比率保持実証 ===")
    
    # 同じ比率で異なる合計値のテスト
    base_weights = [0.4, 0.1]  # 4:1の比率
    
    test_cases = [
        ("比率4:1、合計0.5", [0.4, 0.1]),
        ("比率4:1、合計1.0", [0.8, 0.2]),
        ("比率4:1、合計2.0", [1.6, 0.4]),
        ("比率4:1、合計10.0", [8.0, 2.0])
    ]
    
    choices = ['Strong', 'Weak']
    test_count = 10000
    
    for name, weights in test_cases:
        print(f"\n--- {name} ---")
        print(f"重み: {weights}")
        
        results = Counter()
        for _ in range(test_count):
            selected = random.choices(choices, weights=weights)[0]
            results[selected] += 1
        
        strong_prob = results['Strong'] / test_count
        weak_prob = results['Weak'] / test_count
        ratio = strong_prob / weak_prob if weak_prob > 0 else 0
        
        print(f"結果: Strong={strong_prob:.3f}, Weak={weak_prob:.3f}, 比率={ratio:.1f}:1")

def main():
    print("spawn_weight合計が1を超える場合の動作テスト")
    print("=" * 60)
    
    # Python random.choices() の基本動作確認
    test_weight_normalization()
    
    # CSVパターン分析
    analyze_csv_weight_patterns()
    
    # 比率保持実証
    demonstrate_ratio_preservation()
    
    print("\n" + "=" * 60)
    print("📝 結論:")
    print("1. ✅ random.choices()は重みを自動的に正規化します")
    print("2. ✅ 重みの合計が1を超えても、比率は完全に保たれます")
    print("3. ✅ 重み0.8の選択肢は重み0.2の選択肢より常に4倍選ばれやすくなります")
    print("4. ✅ 合計値に関係なく、重みの相対的な比率が選択確率を決定します")
    print("5. ⚠️  CSVの時間10-40では重み合計が2.0になっていますが、動作に問題ありません")
    print("6. 💡 重みの合計を1にする必要はありませんが、理解しやすさのため1にすることを推奨")

if __name__ == "__main__":
    main()