# ゲーム設定
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
SURVIVAL_TIME = 180

# ワールドサイズ（画面の4倍）
WORLD_WIDTH = SCREEN_WIDTH * 4
WORLD_HEIGHT = SCREEN_HEIGHT * 4

# 色の定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
YELLOW = (255, 255, 0)
PINK = (255, 192, 203)
GRAY = (128, 128, 128)
LIGHT_GRAY = (192, 192, 192)  # テスト用背景の薄いグレー
DARK_GRAY = (48, 48, 48)  # テスト用背景の濃いグレー
MOREDARK_GRAY = (36, 36, 36)  # テスト用背景のさらに濃いグレー

# 所持できる武器の最大数（レベルアップで新規武器を取得できる上限）
MAX_WEAPONS = 4

# 所持できるサブアイテムの最大数（武器上限と同じにする）
MAX_SUBITEMS = MAX_WEAPONS

# レベル上限
MAX_WEAPON_LEVEL = 5
MAX_SUBITEM_LEVEL = 3

# デバッグ・表示設定
DEBUG = False   # デバッグ用ログ出力のON/OFF
SHOW_FPS = True  # FPS表示のON/OFF

# マップ・ステージ設定
USE_CSV_MAP = True    # True: CSVマップ使用, False: ランダム生成背景
TEST_TILE_SIZE = 64    # テスト用背景の市松模様のタイルサイズ

# CSVマップ設定
CSV_MAP_FILE = "map/stage_map.csv"  # CSVマップファイル名
MAP_TILES_WIDTH = 80   # マップの横幅（タイル数）= WORLD_WIDTH / TEST_TILE_SIZE
MAP_TILES_HEIGHT = 45  # マップの縦幅（タイル数）= WORLD_HEIGHT / TEST_TILE_SIZE

# プレイヤーが被弾後に一時的に無敵となる時間（ミリ秒）
INVINCIBLE_MS = 200

# アイテムドロップ確率設定
HEAL_ITEM_DROP_RATE = 0.005    # 0.5%の確率で回復アイテム
BOMB_ITEM_DROP_RATE = 0.002   # 0.2%の確率でボムアイテム（0.01 + 0.002）
MAGNET_ITEM_DROP_RATE = 0.001  # 0.1%の確率でマグネットアイテム

# パーティクル関連の制限（パフォーマンス改善用）
PARTICLE_LIMIT = 120        # これ以上は古いパーティクルから切る（200から120に削減）

# パフォーマンス最適化設定
FULLSCREEN_FPS_THRESHOLD = 2.5  # この倍率以上でFPS調整
FULLSCREEN_FPS = 60  # フルスクリーン時の目標FPS（大画面時）
NORMAL_FPS = 60  # 通常時のFPS
PARTICLE_TRIM_TO = 80       # 切るときに残す数（150から80に削減）

# 画面上に存在可能な経験値ジェムの上限
MAX_GEMS_ON_SCREEN = 100  # 150から100に削減

# HP自然回復設定
NATURAL_HEAL_INTERVAL_MS = 2000  # 自然回復の間隔（ミリ秒）
NATURAL_HEAL_AMOUNT = 0          # 自然回復時の基本回復量（HPサブアイテムレベル分が追加される）

# --- オーディオ基本設定 ---
# 効果音とBGMのデフォルト音量（0.0〜1.0）
DEFAULT_SFX_VOLUME = 0.5
DEFAULT_MUSIC_VOLUME = 0.5

# ガーリック回復設定
GARLIC_HEAL_INTERVAL_MS = 500    # ガーリック回復の間隔（ミリ秒）
GARLIC_HEAL_AMOUNT = 1           # ガーリック回復時の基本回復量（HPサブアイテムレベル分が追加される）

# 回復アイテム設定
HEAL_ITEM_AMOUNT = 0.25          # 回復アイテムの回復量（割合：0.25 = 25%）

# マグネットアイテム設定
MAGNET_EFFECT_DURATION_MS = 3000 # マグネット効果の持続時間（ミリ秒）
MAGNET_FORCE_MULTIPLIER = 3.0    # マグネット効果時のジェム引き寄せ倍率

# 画面揺れエフェクト設定
SCREEN_SHAKE_DURATION_MS = 500   # 画面揺れの持続時間（ミリ秒）
SCREEN_SHAKE_INTENSITY = 10      # 画面揺れの強度（ピクセル）

# レベルアップ時の自動回復量
LEVELUP_HEAL_AMOUNT = 0        # レベルアップ時の回復量

# エネミー画像のHSV調整
ENEMY_IMAGE_HUE_SHIFT = 0.0      # エネミー画像の色相シフト（-1.0～1.0、0.0 = 変更なし）
ENEMY_IMAGE_SATURATION = 0.6     # エネミー画像の彩度（1.0 = 通常、0.8 = 80%）
ENEMY_IMAGE_VALUE = 0.8          # エネミー画像の明度（1.0 = 通常、0.8 = 80%）

# エネミー歩行アニメーション設定
ENEMY_WALK_BOB_AMPLITUDE = 0.5   # 上下振動の振幅（ピクセル、0で無効化）
ENEMY_WALK_BOB_SPEED = 4       # 上下振動の速度（値が大きいほど早い）
ENEMY_WALK_CYCLE_TIME = 1.6      # 1回の歩行サイクル時間（秒）※参考値：2π/BOB_SPEED
ENEMY_WALK_SWAY_AMPLITUDE = 0.8  # 左右振動の振幅（ピクセル）
ENEMY_WALK_SWAY_SPEED = 6.0      # 左右振動の速度
ENEMY_WALK_ROTATION_AMPLITUDE = 2.0  # 回転振動の振幅（度）
ENEMY_WALK_ROTATION_SPEED = 5.0  # 回転振動の速度

# パフォーマンス設定
ENABLE_ENEMY_WALK_ANIMATION = True  # エネミー歩行アニメーションの有効/無効

# 敵同士の回避判定の係数
# 1.0 = 半径和を閾値（重なり不可）
# 0.5 = 中心距離が半分でも許容（半分程度の重なりを許す）
# 値は 0.0（重なり無制限）～1.0（完全衝突回避）の間で設定
ENEMY_COLLISION_SEPARATION_FACTOR = 0.5

# 分離（separation）挙動の設定
# 小さいほど押しのけ量が小さい。デフォルトは 0.6
ENEMY_SEPARATION_STRENGTH = 0.6
# ボス優先の重み（他がボスの場合に非ボスがより強く押しのける）
ENEMY_SEPARATION_BOSS_PRIORITY = 1.5

# 分離（separation）処理の有効/無効フラグ（重い場合は False に切り替え）
ENABLE_ENEMY_SEPARATION = False

# お金・経済システム設定
MONEY_PER_ENEMY_KILLED = 10         # 敵1体撃破あたりの基本報酬
MONEY_PER_LEVEL_BONUS = 50          # レベルアップボーナス
MONEY_PER_SURVIVAL_SECOND = 5       # 1秒生存あたりの報酬
MONEY_GAME_CLEAR_BONUS = 1000       # ゲームクリア時のボーナス
MONEY_CONTINUE_COST = 100           # コンティニューの費用
MONEY_DROP_RATE = 0.1               # 敵がお金を落とす確率（10%）- アイテムボックス用
MONEY_DROP_AMOUNT_MIN = 5           # お金ドロップの最小額 - アイテムボックス用
MONEY_DROP_AMOUNT_MAX = 25          # お金ドロップの最大額 - アイテムボックス用

# 新しいお金アイテム設定（money1～money5）
# money1: 1-10G (出現率40%)
MONEY1_AMOUNT_MIN = 1
MONEY1_AMOUNT_MAX = 10
MONEY1_DROP_RATE = 0.40

# money2: 10-50G (出現率30%)
MONEY2_AMOUNT_MIN = 10
MONEY2_AMOUNT_MAX = 50
MONEY2_DROP_RATE = 0.30

# money3: 50-200G (出現率20%)
MONEY3_AMOUNT_MIN = 50
MONEY3_AMOUNT_MAX = 200
MONEY3_DROP_RATE = 0.20

# money4: 200-1000G (出現率8%)
MONEY4_AMOUNT_MIN = 200
MONEY4_AMOUNT_MAX = 1000
MONEY4_DROP_RATE = 0.08

# money5: 1000-10000G (出現率2%)
MONEY5_AMOUNT_MIN = 1000
MONEY5_AMOUNT_MAX = 10000
MONEY5_DROP_RATE = 0.02

# ボックス別お金ドロップ設定
# Box1: money1～4 (低額寄り)
BOX1_MONEY1_RATE = 0.50  # 50%
BOX1_MONEY2_RATE = 0.30  # 30%
BOX1_MONEY3_RATE = 0.15  # 15%
BOX1_MONEY4_RATE = 0.05  # 5%

# Box2: money3～5 (高額寄り)
BOX2_MONEY3_RATE = 0.60  # 60%
BOX2_MONEY4_RATE = 0.30  # 30%
BOX2_MONEY5_RATE = 0.10  # 10%

# Box3: money4～5 (最高額寄り)
BOX3_MONEY4_RATE = 0.50  # 50%
BOX3_MONEY5_RATE = 0.50  # 50%

# アイテムボックス設定
BOX_SPAWN_RATE = 0.02               # ボックスの基本出現率（2%）
BOX_SPAWN_INTERVAL_MIN = 1000       # ボックス出現の最小間隔（ミリ秒）- 1秒に変更
BOX_SPAWN_INTERVAL_MAX = 5000       # ボックス出現の最大間隔（ミリ秒）- 5秒に変更

# ボックス種類別出現率
BOX1_SPAWN_RATE = 0.6               # box1の出現率（60%）
BOX2_SPAWN_RATE = 0.3              # box2の出現率（30%）
BOX3_SPAWN_RATE = 0.1              # box3の出現率（10%）

# ボックス1の中身（コイン系のみ）
BOX1_COIN_RATE = 1.0                # コイン100%
BOX1_COIN_AMOUNT_MIN = 10           # 最小コイン額
BOX1_COIN_AMOUNT_MAX = 30           # 最大コイン額

# ボックス2の中身（コイン90%、その他10%）
BOX2_COIN_RATE = 0.9                # コイン90%
BOX2_COIN_AMOUNT_MIN = 20           # 最小コイン額
BOX2_COIN_AMOUNT_MAX = 50           # 最大コイン額
BOX2_HEAL_RATE = 0.033              # 回復アイテム3.3%（10%の1/3）
BOX2_BOMB_RATE = 0.033              # ボムアイテム3.3%（10%の1/3）
BOX2_MAGNET_RATE = 0.034            # マグネットアイテム3.4%（10%の1/3、端数調整）

# ボックス3の中身（お金・回復・ボム・マグネット各25%）
BOX3_MONEY_RATE = 0.25              # お金25%
BOX3_HEAL_RATE = 0.25               # 回復アイテム25%
BOX3_BOMB_RATE = 0.25               # ボムアイテム25%
BOX3_MAGNET_RATE = 0.25             # マグネットアイテム25%

# ボックスHP
BOX1_HP = 5                         # box1のHP（軽く叩けば壊れる）
BOX2_HP = 10                        # box2のHP
BOX3_HP = 20                        # box3のHP（少し硬い）
# ボス専用の特別な宝箱
BOX4_HP = 1                        # box4のHP（ボスドロップ用、頑丈）

# ボックスサイズ
BOX_SIZE = 64                       # ボックスの表示サイズ（ピクセル）- 倍のサイズに変更
BOX_COLLISION_SIZE = 56             # ボックスの当たり判定サイズ

# 不可侵領域の境界線設定
BORDER_THICKNESS = 18                # ブロッカー領域の境界線の太さ（ピクセル）

# 武器の不可侵領域設定
# エリア5,9: 通常のブロッカー領域（武器に影響）
# エリア6,7: 貫通可能領域（武器に影響しない）
BLOCKER_AREAS_SOLID = {5, 9}        # 武器に影響するブロッカーエリア
BLOCKER_AREAS_PASSTHROUGH = {6, 7}  # 武器が貫通可能なブロッカーエリア

# 不可侵領域の影響を受ける武器
WEAPONS_AFFECTED_BY_BLOCKERS = {
    "stone",      # 石
    "knife",      # ナイフ
    "axe",        # 斧
    "magic_wand"  # 魔法の杖
}

# 不可侵領域の影響を受けない武器（参考）
# "whip"        # ムチ
# "garlic"      # ガーリック
# "holy_water"  # 聖水
# "rotating_book" # 回転する本
# "thunder"     # 雷

# ノックバック設定
KNOCKBACK_DURATION = 0.1             # ノックバック持続時間（秒）
KNOCKBACK_COOLDOWN_DURATION = 0.8    # ノックバック後のクールダウン時間（秒）