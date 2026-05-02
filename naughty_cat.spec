# -*- mode: python ; coding: utf-8 -*-
a = Analysis(
    ['naughty_cat/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('naughty_cat/assets/cats/*.gif', 'naughty_cat/assets/cats'),
        ('naughty_cat/assets/sounds/*.mp3', 'naughty_cat/assets/sounds'),
        ('naughty_cat/assets/icons/*.ico', 'naughty_cat/assets/icons'),
    ],
    hiddenimports=['PySide6.QtMultimedia'],
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
    name='NaughtyCat',
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
    icon='naughty_cat/assets/icons/cat.ico',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='NaughtyCat',
)
