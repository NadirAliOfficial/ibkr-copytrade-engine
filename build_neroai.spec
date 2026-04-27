# -*- mode: python ; coding: utf-8 -*-
# Pax Americana — PyInstaller spec
# Build: pyinstaller build_neroai.spec

block_cipher = None

a = Analysis(
    ['NeroAI_CopyTrade.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets/pax_americana.png', 'assets'),
    ],
    hiddenimports=[
        'ib_insync',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'tkinter',
        'tkinter.scrolledtext',
        'requests',
        'threading',
        'asyncio',
        'tzdata',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['pyi_rth_eventloop.py'],
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
    # ONEFILE build with a STABLE runtime_tmpdir. The bootloader extracts
    # python3xx.dll + the bundle once into %LOCALAPPDATA%\PaxAmericana
    # and reuses it on every subsequent launch. This gives the user a
    # single self-contained EXE while avoiding the Defender races that
    # plague the default %TEMP%\_MEIxxxxx extract path (which gets a
    # fresh random subdir on every launch and is the root cause of the
    # 'Failed to load Python DLL' crashes).
    name='Pax_Americana',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=['python*.dll', 'vcruntime*.dll', 'msvcp*.dll'],
    runtime_tmpdir='%LOCALAPPDATA%\\PaxAmericana',
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
