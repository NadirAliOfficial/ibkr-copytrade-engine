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
    name='Pax_Americana',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    # UPX disabled: compressing python3xx.dll caused the bundled bootloader
    # to crash with "Failed to load Python DLL" after auto-update on some
    # Windows installs (Defender flags UPX-packed DLLs and quarantines them).
    upx=False,
    upx_exclude=['python*.dll', 'vcruntime*.dll', 'msvcp*.dll'],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
