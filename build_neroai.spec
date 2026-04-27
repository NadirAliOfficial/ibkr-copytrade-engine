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
    [],
    # ONEDIR build: binaries/datas live next to the exe instead of being
    # bundled into a self-extracting onefile. Onefile mode is a Trojan-
    # looking bootloader that extracts python3xx.dll to %TEMP%\_MEIxxxx
    # on every launch — Defender intermittently quarantines that extract,
    # producing 'Failed to load Python DLL' crashes. Onedir is shipped as
    # a folder (zipped for distribution) and is fully self-contained.
    exclude_binaries=True,
    name='Pax_Americana',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Pax_Americana',
)
