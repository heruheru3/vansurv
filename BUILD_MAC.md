# VanSurv - Mac版ビルドガイド

## 前提条件

1. **Python 3.8以降** がインストールされていること
2. **PyInstaller** がインストールされていること
   ```bash
   pip install pyinstaller
   ```
3. **pygame** がインストールされていること
   ```bash
   pip install pygame
   ```

## ビルド手順

### 1. 権限設定（初回のみ）
```bash
# シェルスクリプトに実行権限を付与
chmod +x setup_permissions.sh
./setup_permissions.sh
```

### 2. アプリケーションのビルド
```bash
./create_app.sh
```

### 3. 実行ファイルの確認
ビルドが成功すると、`dist/main`に実行ファイルが作成されます。

```bash
# 実行ファイルのテスト
./dist/main
```

## トラブルシューティング

### 権限エラーが発生する場合
```bash
chmod +x create_app.sh
chmod +x dist/main
```

### PyInstallerが見つからない場合
```bash
pip install --upgrade pyinstaller
```

### Pygameエラーが発生する場合
```bash
pip install --upgrade pygame
```

### アイコンファイルが見つからない場合
アイコンファイル（favicon.ico）が`assets/`フォルダに存在することを確認してください。

## ファイル構成

- `create_app.sh` - Mac版ビルドスクリプト
- `setup_permissions.sh` - 権限設定スクリプト
- `create_exe.bat` - Windows版ビルドスクリプト（参考）

## 注意事項

- Mac版では`.app`バンドルではなく、単一の実行ファイルとして作成されます
- 初回実行時にmacOSのセキュリティ警告が表示される可能性があります
- Gatekeeperを通すには開発者署名が必要です（配布時）

## 配布用パッケージング

配布用には以下のような追加手順が推奨されます：

```bash
# .appバンドルとして作成する場合
pyinstaller --onedir --windowed main.py

# DMGファイルとして配布する場合（別途ツールが必要）
# create-dmg や dmgbuild などを使用
```
