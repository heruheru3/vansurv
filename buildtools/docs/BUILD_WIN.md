# VanSurv - Windows版ビルドガイド

## 前提条件

1. **Python 3.8以降** がインストールされていること
2. **PyInstaller** がインストールされていること
   ```cmd
   pip install pyinstaller
   ```
3. **pygame** がインストールされていること
   ```cmd
   pip install pygame
   ```

## ビルド手順

### 1. バッチファイルの実行
プロジェクトフォルダで`buildtools\scripts\create_exe.bat`をダブルクリックするか、コマンドプロンプトから実行します。

```cmd
buildtools\scripts\create_exe.bat
```

### 2. 実行ファイルの確認
ビルドが成功すると、`dist\heruheru3_vansurv.exe`に実行ファイルが作成されます。

```cmd
# 実行ファイルのテスト
dist\heruheru3_vansurv.exe
```

## トラブルシューティング

### PyInstallerが見つからない場合
```cmd
pip install --upgrade pyinstaller
```

### Pygameエラーが発生する場合
```cmd
pip install --upgrade pygame
```

### アイコンファイルが見つからない場合
アイコンファイル（favicon.ico）が`assets\`フォルダに存在することを確認してください。

### ビルドが途中で失敗する場合
1. コマンドプロンプトを**管理者権限**で実行してみてください
2. Windowsディフェンダーやウイルス対策ソフトがPyInstallerをブロックしていないか確認してください
3. パスに日本語や特殊文字が含まれていないか確認してください

### 実行時エラーが発生する場合
```cmd
# デバッグモードでビルド（コンソール付き）
pyinstaller --noconfirm --onefile --console main.py
```

## ファイル構成

- `buildtools\scripts\create_exe.bat` - Windows版ビルドスクリプト
- `buildtools\scripts\create_app.sh` - Mac版ビルドスクリプト（参考）
- `buildtools\config\main.spec` - PyInstaller設定ファイル
- `buildtools\docs\BUILD_MAC.md` - Mac版ビルドガイド（参考）

## 配布時の注意事項

### セキュリティ警告
- 初回実行時にWindows Defenderの警告が表示される可能性があります
- 信頼できるソフトウェアとしてユーザーに案内してください

### 必要なランタイム
- PyInstallerで作成された実行ファイルは、ターゲットマシンにPythonがインストールされていなくても動作します
- ただし、Visual C++ 再頒布可能パッケージが必要な場合があります

### ファイルサイズ
- one-file形式のため、実行ファイルサイズは比較的大きくなります（50-100MB程度）
- 初回起動時に一時展開が行われるため、起動に少し時間がかかる場合があります

## ビルドオプションの詳細

### 使用されるPyInstallerオプション

- `--noconfirm`: 既存の出力を上書き確認なしで削除
- `--onefile`: 単一の実行ファイルとして作成
- `--windowed`: コンソールウィンドウを表示しない
- `--icon`: 実行ファイルのアイコンを指定
- `--add-data`: ゲームに必要なファイル・フォルダを含める

### カスタマイズ
必要に応じて以下のオプションを追加できます：

```cmd
REM デバッグ情報を含める場合
--debug all

REM 特定のモジュールを除外する場合
--exclude-module tkinter

REM 起動時間を短縮したい場合（複数ファイル形式）
--onedir
```
