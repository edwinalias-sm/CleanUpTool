# -*- mode: python -*-

block_cipher = None

a = Analysis(
    ['main_gui.py'],
    pathex=['.'],
    binaries=[],
    datas=[('cleaner.ico', '.')],  # Ensure cleaner.ico is in the same directory
    hiddenimports=[],  # Add necessary hidden imports if needed
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
    upx=True,  # Set to False if UPX causes issues
    console=False,  # Change to True if a terminal is required
    icon='cleaner.ico'  # Ensure this file exists
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='eod_cleaner',
    distpath='dist',
    workpath='build',
    clean=True
)
