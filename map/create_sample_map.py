"""
サンプルCSVマップ作成スクリプト
80x45マスのサンプルマップを生成
"""

import sys
import os

# constants.pyから設定をインポート
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from map.map_loader import MapLoader

def main():
    print("サンプルCSVマップを作成します...")
    
    # MapLoaderインスタンスを作成
    loader = MapLoader()
    
    # サンプルCSVを作成（mapディレクトリ内に）
    csv_filename = "map/stage_map.csv"
    if loader.create_sample_csv(csv_filename):
        print(f"✓ サンプルCSVファイル '{csv_filename}' を作成しました")
        print(f"  マップサイズ: 80×45 マス")
        print(f"  タイルサイズ: 64×64 ピクセル")
        print(f"  総サイズ: {80*64}×{45*64} ピクセル")
        print()
        print("タイル番号の意味:")
        print("  0: 暗いグレー（デフォルト）")
        print("  1: 濃いグレー")
        print("  2: 通常グレー")  
        print("  3: 薄いグレー")
        print("  4: 茶色（土）")
        print("  5: 濃い緑（森）")
        print("  6: 黄土色（道）")
        print("  7: 青系（水）")
        print("  8: 赤系（危険地帯）")
        print("  9: 中間グレー")
        print()
        print(f"CSVファイルを編集してマップをカスタマイズできます。")
        print(f"main.pyで USE_CSV_MAP = True に設定して使用してください。")
    else:
        print("❌ CSVファイルの作成に失敗しました")

if __name__ == "__main__":
    main()
