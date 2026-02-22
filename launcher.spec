# -*- mode: python ; coding: utf-8 -*-

import platform
import tomllib
from pathlib import Path

with open(Path(SPECPATH) / 'pyproject.toml', 'rb') as f:
    version = tomllib.load(f)['project']['version']

exe_name = f'pocket-scion-osc-{version}-{platform.system().lower()}-{platform.machine().lower()}'

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['rtmidi', 'pythonosc'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name=exe_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
