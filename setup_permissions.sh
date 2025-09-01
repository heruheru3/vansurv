#!/bin/bash

# VanSurv Mac版 - シェルスクリプト実行権限設定
echo "Setting executable permissions for create_app.sh..."

# 現在のディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# create_app.shに実行権限を付与
chmod +x "${SCRIPT_DIR}/create_app.sh"

echo "✅ Permissions set successfully!"
echo "Now you can run: ./create_app.sh"
