# build_neroai.spec

a = Analysis(
    ['NeroAI_CopyTrade.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'ib_insync',
        'requests',
        'tkinter',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name='NeroAI_CopyTrade',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=None,
)