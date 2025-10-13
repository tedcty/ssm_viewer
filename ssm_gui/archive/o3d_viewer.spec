# -*- mode: python ; coding: utf-8 -*-
import sys ; sys.setrecursionlimit(sys.getrecursionlimit() * 5)

a = Analysis(
    ['o3d_viewer.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
    'numpy.core.multiarray',
    'vtkmodules',
    'vtkmodules.util',
    'vtkmodules.util.data_model',
    'vtkmodules.util.execution_model',
    'vtkmodules.util.numpy_support',
    'vtkmodules.qt.QVTKRenderWindowInteractor',
    'vtkmodules.numpy_interface',
    'vtkmodules.numpy_interface.dataset_adapter',
    'vtkmodules.all'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pymeshlab'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='o3d_viewer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ssm3d_viewer',
)
