# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['GenerateCarouselGcode.py'],
    pathex=[],
    binaries=[],
    datas=[('logo.png', '.')],  # Include logo.png in the bundle
    hiddenimports=[
        'matplotlib.backends.backend_tkagg',
        'matplotlib.backends.backend_agg',
        'matplotlib.figure',
        'matplotlib.pyplot',
        'matplotlib.patches',
        'numpy',
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.filedialog',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'shapely',
        'shapely.geometry',
        'shapely.geometry.polygon',
        'json',
        'os'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='GenerateCarouselGcode',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window for GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
