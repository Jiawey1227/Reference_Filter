# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置
使用方法: pyinstaller "AI 文献评分工具.spec"
"""

a = Analysis(
    ['gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        # 不打包缓存文件 — 程序会在首次运行时自动创建
        # 也不打包 key.txt — 用户需要提供自己的 API Key
    ],
    hiddenimports=[
        'openai',
        'pandas',
        'numpy',
        'tqdm',
        'openpyxl',
        'pickle',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter.test',
        'unittest',
        'xmlrpc',
        'pydoc',
    ],
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
    name='AI 文献评分工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI 应用，不显示控制台
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='NONE',  # 如需图标，替换为 icon.ico 路径
)
