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
DARK_GRAY = (36, 36, 36)  # テスト用背景の濃いグレー
MOREDARK_GRAY = (24, 24, 24)  # テスト用背景のさらに濃いグレー

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
USE_STAGE_MAP = False  # True: レトロマップチップ使用, False: 市松模様背景（テスト用）
TEST_TILE_SIZE = 64    # テスト用背景の市松模様のタイルサイズ

# プレイヤーが被弾後に一時的に無敵となる時間（ミリ秒）
INVINCIBLE_MS = 200

# アイテムドロップ確率設定
HEAL_ITEM_DROP_RATE = 0.005    # 0.5%の確率で回復アイテム
BOMB_ITEM_DROP_RATE = 0.002   # 0.2%の確率でボムアイテム（0.01 + 0.002）
MAGNET_ITEM_DROP_RATE = 0.001  # 0.1%の確率でマグネットアイテム

# パーティクル関連の制限（パフォーマンス改善用）
PARTICLE_LIMIT = 200        # これ以上は古いパーティクルから切る

# パフォーマンス最適化設定
FULLSCREEN_FPS_THRESHOLD = 2.5  # この倍率以上でFPS調整
FULLSCREEN_FPS = 60  # フルスクリーン時の目標FPS（大画面時）
NORMAL_FPS = 60  # 通常時のFPS
PARTICLE_TRIM_TO = 150      # 切るときに残す数

# 画面上に存在可能な経験値ジェムの上限
MAX_GEMS_ON_SCREEN = 150

# HP自然回復設定
NATURAL_HEAL_INTERVAL_MS = 2000  # 自然回復の間隔（ミリ秒）
NATURAL_HEAL_AMOUNT = 0          # 自然回復時の基本回復量（HPサブアイテムレベル分が追加される）

# ガーリック回復設定
GARLIC_HEAL_INTERVAL_MS = 500    # ガーリック回復の間隔（ミリ秒）
GARLIC_HEAL_AMOUNT = 1           # ガーリック回復時の基本回復量（HPサブアイテムレベル分が追加される）

# 回復アイテム設定
HEAL_ITEM_AMOUNT = 0.20          # 回復アイテムの回復量（割合：0.20 = 20%）

# マグネットアイテム設定
MAGNET_EFFECT_DURATION_MS = 3000 # マグネット効果の持続時間（ミリ秒）
MAGNET_FORCE_MULTIPLIER = 3.0    # マグネット効果時のジェム引き寄せ倍率

# 画面揺れエフェクト設定
SCREEN_SHAKE_DURATION_MS = 500   # 画面揺れの持続時間（ミリ秒）
SCREEN_SHAKE_INTENSITY = 10      # 画面揺れの強度（ピクセル）

# レベルアップ時の自動回復量
LEVELUP_HEAL_AMOUNT = 20         # レベルアップ時の回復量