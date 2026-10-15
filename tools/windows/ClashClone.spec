# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller recipe for the Windows build (see tools/windows/build_windows.bat).

    pyinstaller --noconfirm --distpath dist --workpath build tools/windows/ClashClone.spec

Makes dist/ClashClone/ : ClashClone.exe + _internal/ (Python, pygame, SDL) +
assets/ (sprites, sounds, music - kept next to the .exe, not inside it, so the
game can find and refresh them exactly like the Python version does).
"""

import glob
import os
import shutil

ROOT = os.path.abspath(os.path.join(SPECPATH, "..", ".."))
SRC = os.path.join(ROOT, "src")
# every game module (some are imported lazily inside functions)
MODULES = sorted(os.path.basename(p)[:-3] for p in glob.glob(os.path.join(SRC, "*.py")))

a = Analysis(
    [os.path.join(SRC, "main.py")],
    pathex=[SRC],
    hiddenimports=MODULES,
    excludes=["numpy", "scipy", "matplotlib", "tkinter", "unittest", "pydoc_data"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ClashClone",
    icon=os.path.join(SPECPATH, "clash.ico"),
    console=False,          # no black console window
    upx=False,              # UPX-packed exes trip antivirus heuristics
)
coll = COLLECT(exe, a.binaries, a.datas, name="ClashClone", upx=False)

# the game's data folder goes beside ClashClone.exe
out = os.path.join(DISTPATH, "ClashClone")
shutil.copytree(os.path.join(ROOT, "assets"), os.path.join(out, "assets"), dirs_exist_ok=True)
for f in ("README.md", "LICENSE", "LICENSE.txt"):
    if os.path.exists(os.path.join(ROOT, f)):
        shutil.copy2(os.path.join(ROOT, f), out)
shutil.copy2(os.path.join(SPECPATH, "READ ME FIRST.txt"), out)
