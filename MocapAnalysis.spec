# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['mocap_gui.py'],
    pathex=[],
    binaries=[('MocapApi.dll', '.')],
    datas=[('take003_chr01.bvh', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pandas', 'jupyter', 'IPython', 'sklearn', 'tensorflow', 'torch', 'cv2', 'seaborn', 'plotly', 'pytest', 'sphinx', 'jedi'],
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
    name='MocapAnalysis',
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
)
