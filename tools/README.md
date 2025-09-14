# Tools Directory

このディレクトリには、ゲーム開発・デバッグ・分析用のツールが格納されています。

## パフォーマンス分析ツール

### analyze_log.py
基本的なパフォーマンスログ分析ツール
- FPS60/50維持可能なエネミー数の分析
- エネミー数別FPS傾向の分析
- CPU使用効率の分析

使用方法:
```bash
cd /path/to/vansurv
python tools/analyze_log.py
```

### analyze_log_detailed.py
詳細なパフォーマンスログ分析ツール
- エネミー数制限効果の分析
- 並列処理効果の分析
- FPS低下時の原因分析
- パフォーマンス統計の詳細表示

使用方法:
```bash
cd /path/to/vansurv
python tools/analyze_log_detailed.py
```

## ゲーム開発ツール

### create_save.py
セーブデータ作成ツール

### enemy_animation_viewer.py
エネミーアニメーション表示ツール

### enemy_image_tool.py
エネミー画像編集ツール

### run_map_editor.py
マップエディターツール

## 注意事項

- 分析ツールを実行する際は、ワークスペースのルートディレクトリから実行してください
- パフォーマンスログファイル（logs/performance_log.csv）が存在することを確認してください
- 分析には pandas ライブラリが必要です