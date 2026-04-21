# -*- coding: utf-8 -*-
import sys, os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect hidden imports
datas = [
    # Backend Python packages
    ('backend', 'backend'),
    # Frontend static files
    ('frontend', 'frontend'),
    # Data directory (database)
    ('data', 'data'),
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'flask', 'flask_cors', 'flask.wrappers', 'flask.templating',
        'openpyxl', 'openpyxl.styles', 'openpyxl.utils',
        'sqlite3', 'werkzeug', 'jinja2', 'markupsafe', 'itsdangerous',
        'click', 'blinker', 'certifi', 'charset_normalizer', 'idna',
        'urllib3', 'requests', 'six', 'python_dateutil', 'pytz', 'et_xmlfile',
        'dateutil', 'dateutil.parser',
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
    [],
    exclude_binaries=True,
    name='猪场管理系统',
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
    icon=None,
    version='version_info.txt',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='猪场管理系统',
)
