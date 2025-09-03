"""
VanSurv マップエディタ起動スクリプト
コマンドラインから簡単に起動できるスクリプト
"""

import os
import sys
import subprocess

def main():
    """メイン関数"""
    # スクリプトの場所を取得
    script_dir = os.path.dirname(os.path.abspath(__file__))
    map_dir = os.path.join(script_dir, "map")
    editor_path = os.path.join(map_dir, "map_editor.py")
    
    print("=== VanSurv Map Editor ===")
    print(f"Starting editor: {editor_path}")
    print()
    
    if not os.path.exists(editor_path):
        print(f"[ERROR] Editor not found: {editor_path}")
        return
    
    try:
        # マップエディタを起動
        os.chdir(map_dir)
        subprocess.run([sys.executable, "map_editor.py"])
    except KeyboardInterrupt:
        print("\n[INFO] Editor interrupted by user")
    except Exception as e:
        print(f"[ERROR] Failed to start editor: {e}")

if __name__ == "__main__":
    main()
