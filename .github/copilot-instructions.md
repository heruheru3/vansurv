# VanSurv - AI Coding Assistant Instructions

VanSurv は Python + pygame で作られた Vampire Survivors ライクなサバイバルアクションゲームです。

## 🏗️ プロジェクト構造

```
vansurv/
├── main.py              # メインゲームループ（2,700行）
├── constants.py         # 全設定・定数（パフォーマンス設定含む）
├── core/               # コアゲームロジック
│   ├── player.py       # プレイヤー管理
│   ├── enemy.py        # 敵とボスロジック
│   ├── game_logic.py   # スポーン・レベルアップ処理
│   ├── collision.py    # 当たり判定システム
│   └── enemy_spawn_manager.py  # CSVベース敵出現管理
├── weapons/            # 武器システム（9種類の武器）
├── effects/            # パーティクル・攻撃・アイテム
├── ui/                # ユーザーインターフェース
├── map/               # CSVマップローダー
├── systems/           # セーブ・パフォーマンス管理
└── tools/             # 開発ツール・テスト・分析
```

## 🎮 ゲーム設計の理解

### アーキテクチャパターン
- **モジュラー設計**: 武器・効果・UI・ステージが分離された構成
- **データドリブン**: CSVファイルから敵ステータス・スポーンルールを読み込み
- **パフォーマンス重視**: 150体の敵でも60FPS維持する並列処理とフレームスキップ

### 重要なゲームループ（main.py）
```python
# フレームスキップ対応の高精度タイミング
# エネミー150体の並列処理
# 描画カリング・パーティクル制限によるパフォーマンス最適化
# デルタタイム補正での滑らかな動作
```

### データファイルの役割
- `data/enemy_stats.csv`: 敵の基本ステータス
- `data/enemy_spawn_rules.csv`: 時間別出現ルール 
- `data/descriptions.json`: UI表示用の説明文
- `map/stage_map.csv`: タイル式レトロマップ

## ⚡ パフォーマンス最適化

### 重要設定（constants.py）
```python
ENABLE_FRAME_SKIP = True        # フレームスキップの有効化
MIN_FPS_THRESHOLD = 45          # 最適化開始のFPS閾値
MAX_ENEMIES_ON_SCREEN = 300     # 敵数上限
DELTA_TIME_CAP = 50.0          # デルタタイム上限
```

### 並列処理の実装
- マルチプロセシングでエネミー弾丸の衝突判定を並列化
- グリッド分割による近傍探索の最適化
- 描画時のカリング（画面外オブジェクトを描画しない）

## 🔧 開発ワークフロー

### テスト実行
```bash
# 特定機能のテスト
python tools/test_spawn_system.py
python tools/test_enemy_distribution.py

# パフォーマンス分析
python tools/analyze_log.py
python tools/analyze_log_detailed.py
```

### デバッグ機能
- **F3**: デバッグモード切替
- **F4**: プレイヤーステータス表示
- **F5**: 攻撃範囲可視化
- **F10**: パフォーマンスログ切り替え

### ビルド（実行ファイル作成）
```bash
# Windows
buildtools/scripts/setup_dev.bat
buildtools/scripts/create_exe.bat

# macOS
buildtools/scripts/setup_permissions.sh
buildtools/scripts/create_app.sh
```

## 🎯 コーディング規約

### 命名規則
- クラス名: PascalCase（`Enemy`, `ExperienceGem`）
- 関数・変数: snake_case（`spawn_enemies`, `game_time`）
- 定数: UPPER_CASE（`MAX_ENEMIES_ON_SCREEN`）

### パフォーマンスパターン
- **フレーム間引き**: `if frame_count % N == 0:` で処理頻度を調整
- **早期リターン**: 条件チェックで無駄な処理をスキップ
- **オブジェクトプール**: `experience_gems`配列での使い回し

### エラーハンドリング
```python
# 軽量なtry-except（ゲームは止めない）
try:
    enemy.update_attack(player)
except Exception:
    pass  # ログ出力せず継続
```

## 🧪 テストパターン

このプロジェクトは**統合テスト重視**：
- `tools/test_*.py`: ゲームシステムの動作確認
- パフォーマンス検証（FPS・メモリ使用量）
- CSV データの整合性チェック
- 武器バランス検証

### テスト追加時の注意
- 実際のゲーム環境での動作を模倣
- パフォーマンス影響を必ず測定
- CSVファイル変更時は関連テストも更新

## 🚨 変更時の注意点

### main.py の編集
- ゲームループは2,700行の巨大ファイル
- パフォーマンスクリティカルな処理が多数
- 変更後は必ずFPS影響をチェック

### constants.py の設定変更
- パフォーマンス設定変更時は `tools/analyze_log.py` でベンチマーク
- デバッグ設定は本番では無効化

### データファイル更新
- CSVファイル変更時は `tools/test_spawn_system.py` で検証
- 新しい敵タイプ追加時は画像も `assets/character/enemy/` に追加

## 💡 よくある作業パターン

### 新武器追加
1. `weapons/` に武器クラス作成
2. `main.py` の武器選択UIに追加
3. `data/descriptions.json` に説明追加
4. `assets/icons/` に武器アイコン追加

### パフォーマンス問題の調査
1. `ENABLE_PERFORMANCE_LOG = True` で測定
2. `tools/analyze_log_detailed.py` で分析
3. ボトルネックを特定後、フレーム間引きや並列処理で対応

### 新敵タイプ追加
1. `data/enemy_stats.csv` にステータス追加
2. `assets/character/enemy/` に画像追加  
3. `tools/test_enemy_distribution.py` でバランス確認