#!/bin/bash

# VanSurv Mac版ビルドスクリプト
# PyInstallerを使用してone-fileの実行ファイルを作成

echo "Building VanSurv for macOS..."

# 現在のディレクトリを取得（プロジェクトルートに移動）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# プロジェクトルートに移動
cd "$SCRIPT_DIR"

# PyInstallerでアプリケーションをビルド
pyinstaller --noconfirm --onefile --windowed --clean --name heruheru3_vansurv \
--hidden-import=colorsys \
--hidden-import=math \
--hidden-import=random \
--hidden-import=json \
--hidden-import=os \
--hidden-import=sys \
--hidden-import=datetime \
--icon "assets/favicon.ico" \
--add-data "constants.py:." \
--add-data "core:core/" \
--add-data "systems:systems/" \
--add-data "ui:ui/" \
--add-data "tools:tools/" \
--add-data "weapons:weapons/" \
--add-data "effects:effects/" \
--add-data "assets:assets/" \
--add-data "data:data/" \
--add-data "map:map/" \
--add-data "save:save/" \
"main.py"

# ビルド結果の確認
if [ -f "dist/heruheru3_vansurv" ]; then
    echo ""
    echo "✅ Build successful!"
    echo "Executable created at: dist/heruheru3_vansurv"
    
    # 実行権限を自動設定
    chmod +x "dist/heruheru3_vansurv"
    echo "🔧 Executable permissions set automatically"
    
    echo ""
    echo "To run the game:"
    echo "  ./dist/heruheru3_vansurv"
else
    echo ""
    echo "❌ Build failed!"
    echo "Please check the output above for errors."
fi
