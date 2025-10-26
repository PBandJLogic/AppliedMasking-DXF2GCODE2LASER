# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['CircumferenceClean.py'],
    pathex=[],
    binaries=[],
    datas=[('logo.png', '.')],  # Include logo.png in the bundle
    hiddenimports=[
        'scipy.optimize',
        'scipy.sparse',
        'scipy.sparse.linalg',
        'matplotlib.backends.backend_tkagg',
        'matplotlib.widgets',
        'serial.tools.list_ports',
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.filedialog',
        'numpy',
        'matplotlib',
        'matplotlib.pyplot',
        'matplotlib.figure',
        'matplotlib.backends',
        'matplotlib.backends.backend_tkagg',
        'matplotlib.backends.backend_tkagg.FigureCanvasTkAgg',
        'matplotlib.backends.backend_tkagg.NavigationToolbar2Tk',
        'matplotlib.widgets.Cursor',
        'serial',
        'serial.tools',
        'serial.tools.list_ports',
        'threading',
        'time',
        're',
        'json',
        'os',
        'datetime',
        'math'
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
    name='CircumferenceClean',
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
    icon='Gcode2LaserIcon.ico',
)
