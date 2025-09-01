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

# 所持できる武器の最大数（レベルアップで新規武器を取得できる上限）
MAX_WEAPONS = 4

# 所持できるサブアイテムの最大数（武器上限と同じにする）
MAX_SUBITEMS = MAX_WEAPONS

# レベル上限
MAX_WEAPON_LEVEL = 5
MAX_SUBITEM_LEVEL = 3

DEBUG = False

# プレイヤーが被弾後に一時的に無敵となる時間（ミリ秒）
INVINCIBLE_MS = 200

# アイテムドロップ確率設定
HEAL_ITEM_DROP_RATE = 0.005    # 0.5%の確率で回復アイテム
BOMB_ITEM_DROP_RATE = 0.002   # 0.2%の確率でボムアイテム（0.01 + 0.002）

# パーティクル関連の制限（パフォーマンス改善用）
PARTICLE_LIMIT = 300        # これ以上は古いパーティクルから切る
PARTICLE_TRIM_TO = 220      # 切るときに残す数

# 画面上に存在可能な経験値ジェムの上限
MAX_GEMS_ON_SCREEN = 200

# HP自然回復設定
NATURAL_HEAL_INTERVAL_MS = 2000  # 自然回復の間隔（ミリ秒）
NATURAL_HEAL_AMOUNT = 0          # 自然回復時の基本回復量（HPサブアイテムレベル分が追加される）

# ガーリック回復設定
GARLIC_HEAL_INTERVAL_MS = 500    # ガーリック回復の間隔（ミリ秒）
GARLIC_HEAL_AMOUNT = 1           # ガーリック回復時の基本回復量（HPサブアイテムレベル分が追加される）

# 回復アイテム設定
HEAL_ITEM_AMOUNT = 0.20          # 回復アイテムの回復量（割合：0.20 = 20%）

# レベルアップ時の自動回復量
LEVELUP_HEAL_AMOUNT = 20         # レベルアップ時の回復量