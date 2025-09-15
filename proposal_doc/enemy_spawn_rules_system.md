# エネミー出現ルール外部定義化システム提案

## 概要

現在のハードコードされた敵出現ロジックを、CSVファイルベースの外部定義システムに置き換える提案です。これにより、プログラマー以外でも敵の出現パターンを調整でき、バランス調整やA/Bテストが容易になります。

## 現在の問題点

### 1. ハードコードされた出現ロジック
```python
# core/enemy.py内のget_random_enemy_no()
if game_time <= 30:  # 序盤（0-30秒）
    # レベル1の敵を優先
    candidates = [no for no in available_enemies 
                 if cls._enemy_stats[no]['level'] == 1]
elif game_time <= 70:  # 中盤（31-70秒）
    # 複雑な重み付けロジック...
```

### 2. 変更時の影響範囲
- バランス調整にコード変更が必要
- 複数のパターンのテストが困難
- デザイナー・プランナーが直接調整できない

## 提案システム

### 1. 新しいCSVファイル構造

#### `data/enemy_spawn_rules.csv`
```csv
rule_id,start_time,end_time,enemy_no_list,spawn_weight,spawn_frequency,strength_multiplier,size_multiplier,enabled,description
1,0,30,"1,2,6,7",0.8,1.0,1.0,1.0,true,序盤・基本敵メイン
2,0,30,"3,8",0.2,0.5,1.0,1.0,true,序盤・少し強い敵
3,30,70,"1,2,6,7",0.4,1.2,1.0,1.0,true,中盤・基本敵継続
4,30,70,"3,4,8,9",0.3,0.8,1.1,1.0,true,中盤・中レベル敵
5,30,70,"11,12,16,17",0.3,0.6,1.0,1.0,true,中盤・射撃敵登場
6,70,-1,"1,6",0.2,1.5,1.0,1.0,true,終盤・基本敵継続
7,70,-1,"3,4,8,9",0.3,1.0,1.2,1.1,true,終盤・中レベル敵強化
8,70,-1,"11,12,13,16,17,18",0.3,0.8,1.1,1.0,true,終盤・射撃敵強化
9,70,-1,"5,10,15,20",0.2,0.4,1.5,1.2,true,終盤・最強敵登場
10,120,-1,"13,14,18,19",0.15,0.3,2.0,1.4,true,超終盤・高レベル射撃敵
11,150,-1,"5,10,15,20",0.3,0.6,2.5,1.5,true,超終盤・最強敵強化
```

#### CSVカラム定義

| カラム名 | 型 | 説明 | 例 |
|----------|---|------|-----|
| `rule_id` | int | ルールの一意識別子 | 1, 2, 3... |
| `start_time` | int | 出現開始時間（秒） | 0, 30, 70 |
| `end_time` | int | 出現終了時間（秒、-1=無制限） | 30, 70, -1 |
| `enemy_no_list` | string | 対象enemy_noのリスト（カンマ区切り） | "1,2,6,7" |
| `spawn_weight` | float | このルールの出現重み（0.0-1.0） | 0.8, 0.3 |
| `spawn_frequency` | float | 出現頻度倍率（基準値に対する倍率） | 1.0, 1.5 |
| `strength_multiplier` | float | 強さ倍率（HP・攻撃力） | 1.0, 1.5, 2.0 |
| `size_multiplier` | float | サイズ倍率（image_size） | 1.0, 1.2, 1.5 |
| `enabled` | bool | ルールの有効/無効 | true, false |
| `description` | string | ルールの説明 | "序盤・基本敵メイン" |

### 2. 実装アーキテクチャ

#### A. EnemySpawnManager クラス
```python
class EnemySpawnManager:
    def __init__(self):
        self.spawn_rules = []
        self.load_spawn_rules()
    
    def load_spawn_rules(self):
        """spawn_rules.csvから読み込み"""
        # CSVファイルを読み込み、self.spawn_rulesに格納
    
    def get_active_rules(self, game_time):
        """現在時刻で有効なルールを取得"""
        active_rules = []
        for rule in self.spawn_rules:
            if not rule['enabled']:
                continue
            if rule['start_time'] <= game_time:
                if rule['end_time'] == -1 or game_time <= rule['end_time']:
                    active_rules.append(rule)
        return active_rules
    
    def select_enemy_no(self, game_time):
        """重み付き選択でenemy_noを決定"""
        active_rules = self.get_active_rules(game_time)
        if not active_rules:
            return 1  # フォールバック
        
        # 重み付き選択ロジック
        candidates = []
        weights = []
        for rule in active_rules:
            enemy_nos = [int(x.strip()) for x in rule['enemy_no_list'].split(',')]
            for enemy_no in enemy_nos:
                candidates.append({
                    'enemy_no': enemy_no,
                    'rule': rule
                })
                weights.append(rule['spawn_weight'])
        
        if candidates:
            selected = random.choices(candidates, weights=weights)[0]
            return selected['enemy_no'], selected['rule']
        return 1, None
    
    def get_enemy_modifiers(self, rule):
        """ルールから倍率情報を取得"""
        if rule is None:
            return 1.0, 1.0  # デフォルト倍率
        return rule['strength_multiplier'], rule['size_multiplier']
```

#### B. Enemy クラスの拡張
```python
class Enemy:
    def __init__(self, screen, game_time, spawn_x=None, spawn_y=None, 
                 spawn_side=None, is_boss=False, boss_level=1, boss_type=None, 
                 boss_image_file=None, boss_stats_key=None, boss_no=None, 
                 enemy_no=None, strength_multiplier=1.0, size_multiplier=1.0):
        # 既存の初期化処理...
        
        # 倍率の適用
        self.strength_multiplier = strength_multiplier
        self.size_multiplier = size_multiplier
    
    def setup_enemy_stats(self):
        # 既存のステータス設定...
        
        # 倍率の適用
        self.hp = int(self.hp * self.strength_multiplier)
        self.max_hp = int(self.max_hp * self.strength_multiplier)
        self.damage = int(self.damage * self.strength_multiplier)
        
        # サイズ倍率の適用
        if hasattr(self, 'size_multiplier') and self.size_multiplier != 1.0:
            self.size = int(self.size * self.size_multiplier)
```

#### C. メインループの修正
```python
# main.py内の敵生成部分
spawn_manager = EnemySpawnManager()  # グローバルに初期化

# 敵生成時
enemy_no, rule = spawn_manager.select_enemy_no(game_time)
strength_mult, size_mult = spawn_manager.get_enemy_modifiers(rule)

enemy = Enemy(screen, game_time, spawn_x=sx, spawn_y=sy, 
              enemy_no=enemy_no, 
              strength_multiplier=strength_mult, 
              size_multiplier=size_mult)
```

### 3. 段階的実装計画

#### Phase 1: 基本システム構築（1-2日）
1. `EnemySpawnManager` クラスの実装
2. CSV読み込み機能
3. 基本的な重み付き選択ロジック
4. 既存システムとの互換性確保

#### Phase 2: 倍率システム（1日）
1. `strength_multiplier` の実装（HP・攻撃力）
2. `size_multiplier` の実装（サイズ・当たり判定）
3. 倍率適用のテストとバランス調整

#### Phase 3: 高度な機能（2-3日）
1. 複雑な条件分岐（プレイヤーレベル依存など）
2. イベント単位の特殊出現ルール
3. A/Bテスト用の複数ルールセット切り替え

#### Phase 4: ツール・UI（2-3日）
1. バランス調整用のリアルタイム編集ツール
2. 出現ルールの可視化ダッシュボード
3. デバッグ・分析用ログ出力

### 4. 利点・効果

#### A. 開発効率の向上
- **コード変更不要**: バランス調整がCSV編集のみで完結
- **高速イテレーション**: ゲーム再起動なしでの調整（将来的）
- **並行作業**: プログラマーとデザイナーの作業分離

#### B. バランス調整の柔軟性
- **時間軸での細かい制御**: 秒単位での出現パターン変更
- **段階的強化**: 倍率システムによる敵の段階的強化
- **A/Bテスト対応**: ルールセットの簡単な切り替え

#### C. デバッグ・分析の向上
- **可視性**: 現在適用中のルールが明確
- **トレーサビリティ**: 変更履歴の管理が容易
- **データ分析**: 出現パターンと難易度の関係分析

### 5. 想定される課題と対策

#### A. パフォーマンス
**課題**: CSV読み込みとルール評価のオーバーヘッド  
**対策**: 
- 起動時の一回読み込み + キャッシュ
- ルール評価の最適化（時間範囲インデックス）

#### B. 複雑性の管理
**課題**: ルール数増加による設定の複雑化  
**対策**: 
- テンプレート機能（基本パターンの提供）
- 検証ツール（ルールの整合性チェック）

#### C. 既存システムとの互換性
**課題**: 既存のハードコードロジックとの競合  
**対策**: 
- 段階的移行（フラグでの切り替え）
- フォールバック機能（CSV読み込み失敗時）

### 6. サンプル設定例

#### 難易度カーブの例
```csv
# 序盤（0-30秒）: 易しい敵のみ
1,0,30,"1,2,6,7",1.0,1.0,1.0,1.0,true,序盤基本

# 中盤（30-90秒）: 射撃敵追加、徐々に強化
2,30,60,"1,2,6,7",0.6,1.2,1.0,1.0,true,中盤基本継続
3,30,60,"11,16",0.4,0.6,1.0,1.0,true,中盤射撃敵導入
4,60,90,"3,4,8,9",0.5,1.0,1.2,1.1,true,中盤強化敵

# 終盤（90秒以降）: 最強敵登場、大幅強化
5,90,-1,"5,10,15,20",0.3,0.8,2.0,1.5,true,終盤最強敵
6,120,-1,"13,14,18,19",0.4,1.0,2.5,1.3,true,超終盤射撃強化
```

### 7. 次のステップ

1. **基本システムの実装**: `EnemySpawnManager` の作成
2. **CSV定義の詳細化**: 具体的なルール設定の作成
3. **テスト環境の構築**: 新旧システムの比較テスト
4. **段階的移行**: 既存システムからの置き換え

この提案により、エネミー出現システムが大幅に柔軟化され、継続的なバランス調整とコンテンツ拡張が容易になります。