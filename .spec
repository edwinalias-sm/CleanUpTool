# -*- mode: python -*-

block_cipher = None

a = Analysis(
    ['main_gui.py'],
    pathex=['.'],
    binaries=[],
    datas=[('cleaner.png', '.')],  # Ensure cleaner.png is in the same directory as the script
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='eod_cleaner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='cleaner.png'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    a.scripts,  # Ensure dependencies are included
    strip=False,
    upx=True,
    upx_exclude=[],
    name='eod_cleaner',
    distpath='build'  # Output directory
)
