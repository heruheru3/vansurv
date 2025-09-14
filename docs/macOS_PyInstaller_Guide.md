# macOS PyInstaller ビルド対応について

## 概要

macOS環境でPyInstallerを使用してゲームをビルドする際の権限問題を解決するため、ファイル出力パスを相対パスから絶対パスに変更しました。

## 変更内容

### 1. 新しいファイルパス管理システム

`utils/file_paths.py` を追加し、OS固有の適切なファイル出力ディレクトリを取得する機能を実装しました。

**対応OS別のファイル出力場所:**

- **Windows**: 
  - ログ: `%APPDATA%\VanSurv\logs\`
  - セーブ: `%USERPROFILE%\Documents\VanSurv\save\`

- **macOS**: 
  - ログ: `~/Library/Application Support/VanSurv/logs/`
  - セーブ: `~/Documents/VanSurv/save/`

- **Linux**: 
  - ログ: `~/.local/share/VanSurv/logs/`
  - セーブ: `~/Documents/VanSurv/save/` (Documents がない場合は `~/VanSurv/save/`)

### 2. 権限エラー対応

- ディレクトリ作成前の書き込み権限チェック
- 権限がない場合のフォールバック処理
- エラーハンドリングの強化

### 3. 修正されたファイル

- `utils/file_paths.py` - 新規作成
- `systems/performance_logger.py` - 絶対パス対応
- `systems/save_system.py` - 絶対パス対応
- `heruheru3_vansurv.spec` - utils/ ディレクトリの追加

## PyInstaller ビルド手順（macOS）

1. **依存関係のインストール**:
   ```bash
   pip install pygame pyinstaller
   # psutilはオプション（パフォーマンス測定用）
   pip install psutil
   ```

2. **ビルド実行**:
   ```bash
   pyinstaller heruheru3_vansurv.spec
   ```

3. **生成されたアプリの確認**:
   ```bash
   # アプリケーションを実行
   ./dist/heruheru3_vansurv.app/Contents/MacOS/heruheru3_vansurv
   ```

## 権限問題の解決方法

### macOS Catalina以降でのセキュリティ対応

1. **Gatekeeper対応**: 
   初回実行時に「開発元が未確認」のダイアログが表示される場合があります。
   - システム環境設定 > セキュリティとプライバシー で許可

2. **ファイルアクセス権限**:
   初回起動時にファイル書き込み権限の確認ダイアログが表示されます。
   - Documents フォルダへのアクセス許可が必要

### トラブルシューティング

**問題**: アプリがサイレントに終了する
**解決**: 
- ターミナルから直接実行してエラーメッセージを確認
- Console.app でシステムログを確認

**問題**: セーブデータが保存されない
**解決**:
- Documents フォルダの書き込み権限を確認
- `~/Documents/VanSurv/` フォルダが作成されているか確認

## 開発環境での動作

開発環境（PyInstallerでビルドしていない状態）では、従来通りの相対パス（`logs/`, `save/`）が使用されます。

## テスト方法

ファイルパス機能のテスト:
```bash
python utils/file_paths.py
```

このコマンドで以下が確認できます:
- OS固有のパス取得
- ディレクトリ作成
- ファイル書き込み権限

## 注意事項

1. **セーブデータの場所**: ユーザーのDocumentsフォルダ内に作成されるため、アンインストール時に手動削除が必要
2. **ログデータ**: アプリケーションデータフォルダに保存されるため、通常は自動的にクリーンアップされる
3. **権限確認**: 初回起動時にmacOSのセキュリティダイアログが表示される可能性がある

## 今後の改善点

- コード署名の追加（配布時）
- アプリケーション証明書の取得
- App Store配布対応（必要に応じて）