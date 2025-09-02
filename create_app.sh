#!/bin/bash

# VanSurv Mac版ビルドスクリプト
# PyInstallerを使用してone-fileの実行ファイルを作成

echo "Building VanSurv for macOS..."

# 現在のディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# PyInstallerでアプリケーションをビルド
pyinstaller --noconfirm --onefile --windowed --clean --name heruheru3_vansurv \
--hidden-import=colorsys \
--hidden-import=math \
--hidden-import=random \
--hidden-import=json \
--hidden-import=os \
--hidden-import=sys \
--icon "${SCRIPT_DIR}/assets/favicon.ico" \
--add-data "${SCRIPT_DIR}/__init__.py:." \
--add-data "${SCRIPT_DIR}/constants.py:." \
--add-data "${SCRIPT_DIR}/enemy.py:." \
--add-data "${SCRIPT_DIR}/player.py:." \
--add-data "${SCRIPT_DIR}/resources.py:." \
--add-data "${SCRIPT_DIR}/stage.py:." \
--add-data "${SCRIPT_DIR}/subitems.py:." \
--add-data "${SCRIPT_DIR}/ui.py:." \
--add-data "${SCRIPT_DIR}/collision.py:." \
--add-data "${SCRIPT_DIR}/game_logic.py:." \
--add-data "${SCRIPT_DIR}/game_utils.py:." \
--add-data "${SCRIPT_DIR}/weapons:weapons/" \
--add-data "${SCRIPT_DIR}/effects:effects/" \
--add-data "${SCRIPT_DIR}/assets:assets/" \
--add-data "${SCRIPT_DIR}/data:data/" \
"${SCRIPT_DIR}/main.py"

# ビルド結果の確認
if [ -f "${SCRIPT_DIR}/dist/heruheru3_vansurv" ]; then
    echo ""
    echo "✅ Build successful!"
    echo "Executable created at: ${SCRIPT_DIR}/dist/heruheru3_vansurv"
    
    # 実行権限を自動設定
    chmod +x "${SCRIPT_DIR}/dist/heruheru3_vansurv"
    echo "🔧 Executable permissions set automatically"
    
    echo ""
    echo "To run the game:"
    echo "  ./dist/heruheru3_vansurv"
else
    echo ""
    echo "❌ Build failed!"
    echo "Please check the output above for errors."
fi
