import pygame
import os

# キャッシュ
_icon_cache = {}
_font_cache = {}
_jp_font_path = None
_sound_cache = {}

DEFAULT_ICON_NAMES = ['sword','magic_wand','stone','whip','holy_water','garlic',
                      'axe','thunder','knife','rotating_book',
                      # subitem crystals
                      'hp','base_damage','defense','speed','effect_range','effect_time','extra_projectiles','projectile_speed']

def load_icons(size=32, icon_names=None, icons_dir=None):
    """指定フォルダからアイコンPNGを読み込み、指定サイズにリサイズして辞書で返す。
    読み込み失敗時は None を値にすることで呼び出し側でフォールバック可能にする。
    キャッシュはファイルパスとサイズで簡易的に保持する。
    """
    if icon_names is None:
        icon_names = DEFAULT_ICON_NAMES
    if icons_dir is None:
        icons_dir = os.path.join(os.path.dirname(__file__), 'assets', 'icons')

    icons = {}
    for nm in icon_names:
        key = f"{nm}_{size}"
        if key in _icon_cache:
            icons[nm] = _icon_cache[key]
            continue
        p = os.path.join(icons_dir, f"{nm}.png")
        try:
            surf = pygame.image.load(p).convert_alpha()
            # ピクセルアート向けにスムージングを避け、nearest-neighborでリサイズ
            if surf.get_width() != size or surf.get_height() != size:
                try:
                    surf = pygame.transform.scale(surf, (size, size))
                except Exception:
                    pass
            _icon_cache[key] = surf
            icons[nm] = surf
        except Exception:
            _icon_cache[key] = None
            icons[nm] = None
    return icons

# --- フォント管理 ---
def get_font(size):
    """キャッシュ済みの pygame Font を返す。存在しなければ生成してキャッシュする。"""
    key = f"font_{size}"
    if key in _font_cache:
        return _font_cache[key]
    global _jp_font_path
    if _jp_font_path is None:
        try:
            proj_font = os.path.join(os.path.dirname(__file__), 'assets', 'fonts', 'NotoSansCJKjp-DemiLight.ttf')
            if os.path.exists(proj_font):
                _jp_font_path = proj_font
            else:
                # try common system fonts
                candidates = ["Meiryo", "Yu Gothic", "MS Gothic", "NotoSansCJKjp-Regular", "Noto Sans CJK JP", "IPAPGothic", "TakaoPGothic"]
                found = None
                for name in candidates:
                    try:
                        p = pygame.font.match_font(name)
                        if p:
                            found = p
                            break
                    except Exception:
                        continue
                _jp_font_path = found
        except Exception:
            _jp_font_path = None
    try:
        if _jp_font_path:
            f = pygame.font.Font(_jp_font_path, size)
        else:
            f = pygame.font.Font(None, size)
    except Exception:
        try:
            f = pygame.font.SysFont(None, size)
        except Exception:
            f = None
    _font_cache[key] = f
    return f

# --- サウンド管理 ---
def load_sound(name, sounds_dir=None):
    """名前（拡張子なし）からサウンドを読み込み、キャッシュして返す。失敗時は None。"""
    if sounds_dir is None:
        sounds_dir = os.path.join(os.path.dirname(__file__), 'assets', 'sfx')
    base = os.path.join(sounds_dir, name)
    # try common extensions
    for ext in ('.wav', '.ogg', '.mp3'):
        path = base + ext
        if os.path.exists(path):
            if path in _sound_cache:
                return _sound_cache[path]
            try:
                snd = pygame.mixer.Sound(path)
                _sound_cache[path] = snd
                return snd
            except Exception:
                _sound_cache[path] = None
                return None
    return None

def load_sounds(names, sounds_dir=None):
    res = {}
    for n in names:
        res[n] = load_sound(n, sounds_dir=sounds_dir)
    return res

# --- 全体プリロード ---
def preload_all(icon_size=32, icon_names=None, font_sizes=None, sound_names=None, icons_dir=None, sounds_dir=None):
    """よく使うリソースを一括でプリロードするユーティリティ。
    pygame.init() を呼んだ後で実行してください。
    """
    # icons
    if icon_names is None:
        icon_names = DEFAULT_ICON_NAMES
    if icons_dir is None:
        icons_dir = os.path.join(os.path.dirname(__file__), 'assets', 'icons')
    for nm in icon_names:
        load_icons(size=icon_size, icon_names=[nm], icons_dir=icons_dir)

    # fonts
    if font_sizes is None:
        font_sizes = [14,18, 22, 28, 30, 34, 36, 40, 72]
    for s in font_sizes:
        get_font(s)

    # sounds
    if sound_names:
        load_sounds(sound_names, sounds_dir=sounds_dir)

    return {
        'icons': {n: _icon_cache.get(f"{n}_{icon_size}") for n in icon_names},
        'fonts': {f: _font_cache.get(f"font_{f}") for f in font_sizes},
        'sounds': _sound_cache.copy()
    }

# エクスポート用
__all__ = ['load_icons', 'get_font', 'load_sound', 'load_sounds', 'preload_all']
