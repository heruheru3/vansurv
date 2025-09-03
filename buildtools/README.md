# VanSurv - ビルドツール

このディレクトリには、VanSurvゲームのビルドに関連するツールとドキュメントが格納されています。

## ディレクトリ構造

```
buildtools/
├── README.md              # このファイル
├── scripts/               # ビルド用スクリプト
│   ├── create_exe.bat     # Windows用実行ファイル作成
│   ├── create_app.sh      # Mac用実行ファイル作成
│   ├── setup_dev.bat      # Windows開発環境セットアップ
│   └── setup_permissions.sh  # Mac権限設定
├── config/                # ビルド設定ファイル
│   └── main.spec          # PyInstaller設定
├── docs/                  # ビルドガイド
│   ├── BUILD_WIN.md       # Windows版ビルドガイド
│   └── BUILD_MAC.md       # Mac版ビルドガイド
├── heruheru3_vansurv.exe/ # Windows用ビルド出力（自動生成）
└── main/                  # Mac用ビルド出力（自動生成）
```

## 使用方法

### Windows版のビルド

1. 開発環境のセットアップ（初回のみ）:
   ```cmd
   buildtools\scripts\setup_dev.bat
   ```

2. 実行ファイルの作成:
   ```cmd
   buildtools\scripts\create_exe.bat
   ```

### Mac版のビルド

1. 権限設定（初回のみ）:
   ```bash
   chmod +x buildtools/scripts/setup_permissions.sh
   ./buildtools/scripts/setup_permissions.sh
   ```

2. 実行ファイルの作成:
   ```bash
   ./buildtools/scripts/create_app.sh
   ```

## 詳細なガイド

- Windows版: [buildtools/docs/BUILD_WIN.md](docs/BUILD_WIN.md)
- Mac版: [buildtools/docs/BUILD_MAC.md](docs/BUILD_MAC.md)

## 注意事項

- すべてのスクリプトはプロジェクトルートから実行されます
- PyInstaller設定ファイルは `buildtools/config/main.spec` に保存されます
- ビルド出力は `dist/` ディレクトリに生成されます
