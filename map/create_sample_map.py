"""
サンプルCSVマップ作成スクリプト
80x45マスのサンプルマップを生成
"""

import sys
import os

# パス設定を追加（実行場所に関係なく動作させるため）
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# 親ディレクトリ（ルートディレクトリ）をパスに追加
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# mapディレクトリもパスに追加（map内からの実行時に必要）
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# インポート（実行場所に応じて調整）
try:
    # mapディレクトリ内から実行する場合
    from map_loader import MapLoader
    print(f"[INFO] MapLoaderをmap_loaderからインポートしました")
except ImportError:
    try:
        # ルートディレクトリから実行する場合
        from map.map_loader import MapLoader
        print(f"[INFO] MapLoaderをmap.map_loaderからインポートしました")
    except ImportError as e:
        print(f"❌ MapLoaderのインポートに失敗しました: {e}")
        print(f"現在のディレクトリ: {current_dir}")
        print(f"親ディレクトリ: {parent_dir}")
        print(f"Pythonパス: {sys.path[:3]}...")  # 最初の3つだけ表示
        sys.exit(1)

def main():
    print("サンプルCSVマップを作成します...")
    
    # MapLoaderインスタンスを作成
    loader = MapLoader()
    
    # 実行場所に応じてCSVファイルのパスを決定
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(current_dir) == 'map':
        # mapディレクトリ内から実行する場合は同じディレクトリに出力
        csv_filename = os.path.join(current_dir, "stage_map.csv")
        print(f"[INFO] 出力先: {csv_filename}")
    else:
        # ルートディレクトリから実行する場合はmapディレクトリに出力
        map_dir = os.path.join(current_dir, "map")
        csv_filename = os.path.join(map_dir, "stage_map.csv")
        print(f"[INFO] 出力先: {csv_filename}")
        # mapディレクトリが存在しない場合は作成
        if not os.path.exists(map_dir):
            os.makedirs(map_dir)
    
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
