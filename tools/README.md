# Tools Directory# Tools Directory



このディレクトリには、ゲーム開発・デバッグ・分析用のツールが格納されています。このディレクトリには、ゲーム開発・デバッグ・分析用のツールが格納されています。



## パフォーマンス分析ツール## パフォーマンス分析ツール



### analyze_log.py### analyze_log.py

基本的なパフォーマンスログ分析ツール基本的なパフォーマンスログ分析ツール

- FPS60/50維持可能なエネミー数の分析- FPS60/50維持可能なエネミー数の分析

- エネミー数別FPS傾向の分析- エネミー数別FPS傾向の分析

- CPU使用効率の分析- CPU使用効率の分析



使用方法:使用方法:

```bash```bash

cd /path/to/vansurvcd /path/to/vansurv

python tools/analyze_log.pypython tools/analyze_log.py

``````



### analyze_log_detailed.py### analyze_log_detailed.py

詳細なパフォーマンスログ分析ツール詳細なパフォーマンスログ分析ツール

- エネミー数制限効果の分析- エネミー数制限効果の分析

- 並列処理効果の分析- 並列処理効果の分析

- FPS低下時の原因分析- FPS低下時の原因分析

- パフォーマンス統計の詳細表示- パフォーマンス統計の詳細表示



使用方法:使用方法:

```bash```bash

cd /path/to/vansurvcd /path/to/vansurv

python tools/analyze_log_detailed.pypython tools/analyze_log_detailed.py

``````



## エネミー出現システム テストツール## ゲーム開発ツール



### test_spawn_system.py### create_save.py

エネミー出現ルール外部定義化システムの基本機能テストセーブデータ作成ツール

- CSVルールの読み込み確認

- 時間帯別のアクティブルール確認### enemy_animation_viewer.py

- 敵選択と倍率適用のテストエネミーアニメーション表示ツール



### test_enemy_distribution.py### enemy_image_tool.py

enemy_no_list内での敵選択比率テストエネミー画像編集ツール

- 重み付きランダム選択の動作確認

- 敵別選択回数の統計分析### run_map_editor.py

- 理論値との比較検証マップエディターツール



### test_spawn_frequency.py## 注意事項

spawn_frequency倍率の動作テスト

- 各時間帯での平均spawn_frequency計算- 分析ツールを実行する際は、ワークスペースのルートディレクトリから実行してください

- スポーンタイミングのシミュレーション- パフォーマンスログファイル（logs/performance_log.csv）が存在することを確認してください

- 出現頻度変化の確認- 分析には pandas ライブラリが必要です

### analyze_spawn_frequency_unit.py
spawn_frequencyの単位と出現数の詳細分析
- spawn_frequencyの仕組み解説
- 1秒あたりの出現回数計算
- 異なる倍率値での効果比較

使用方法:
```bash
cd /path/to/vansurv/tools
python test_spawn_system.py
python test_enemy_distribution.py
python test_spawn_frequency.py
python analyze_spawn_frequency_unit.py
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
- エネミー出現システムテストツールは、toolsディレクトリから実行してください
- パフォーマンスログファイル（logs/performance_log.csv）が存在することを確認してください
- 分析には pandas ライブラリが必要です