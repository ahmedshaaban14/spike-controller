from PyInstaller.utils.hooks import collect_all, collect_data_files, copy_metadata

datas = [('hub/hub_controller.py', 'hub')]
binaries = []
hiddenimports = ['pybricksdev._vendored.mpy_tool_v6_3', 'bleak.backends.winrt.client']
datas += collect_data_files('pybricksdev')
for package in ('mpy_cross_v5', 'mpy_cross_v6'):
    d, b, h = collect_all(package)
    datas += d
    binaries += b
    hiddenimports += h
datas += copy_metadata('pybricksdev')
a = Analysis(['launch.py'], pathex=[], binaries=binaries, datas=datas,
             hiddenimports=hiddenimports, hookspath=[], hooksconfig={},
             runtime_hooks=[], excludes=['tkinter', 'matplotlib', 'numpy', 'pandas',
                                        'scipy', 'PyQt5', 'PyQt6', 'pybricksdev.cli'],
             noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='SPIKE Controller',
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
          console=False, disable_windowed_traceback=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='SPIKE Controller')
