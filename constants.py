# ゲーム設定
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
SURVIVAL_TIME = 100

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