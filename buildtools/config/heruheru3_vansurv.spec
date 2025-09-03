# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['..\\..\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('constants.py', '.'), ('enemy.py', '.'), ('player.py', '.'), ('resources.py', '.'), ('stage.py', '.'), ('subitems.py', '.'), ('ui.py', '.'), ('collision.py', '.'), ('game_logic.py', '.'), ('game_utils.py', '.'), ('box.py', '.'), ('save_system.py', '.'), ('performance_config.py', '.'), ('weapons', 'weapons/'), ('effects', 'effects/'), ('assets', 'assets/'), ('data', 'data/'), ('map', 'map/'), ('save', 'save/')],
    hiddenimports=['colorsys', 'math', 'random', 'json', 'os', 'sys', 'datetime'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='heruheru3_vansurv',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets\\favicon.ico'],
)
