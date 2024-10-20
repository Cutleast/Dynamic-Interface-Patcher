"""
Copyright (c) Cutleast

Build script for cx_freeze. Run with `python setup.py build_exe`.
"""

import os
import shutil
from pathlib import Path

from cx_Freeze import Executable, setup

# Application details
APPNAME = "Dynamic Interface Patcher"
VERSION = "2.1.0"
AUTHOR = "Cutleast"
LICENSE = "Attribution-NonCommercial-NoDerivatives 4.0 International"
DIST_FOLDER = Path("dist").resolve()
FOMOD_FOLDER = Path("fomod").resolve()
OUTPUT_FOLDER = Path("DIP_with_fomod").resolve() / "fomod"
OBSOLETE_ITEMS: list[Path] = [DIST_FOLDER / "lib" / "qtpy" / "tests"]
ADDITIONAL_ITEMS: dict[Path, Path] = {
    Path("res") / "7-zip": DIST_FOLDER / "7-zip",
    Path("res") / "ffdec": DIST_FOLDER / "ffdec",
    Path("res") / "jre.7z": DIST_FOLDER / "jre.7z",
    Path("res") / "xdelta": DIST_FOLDER / "xdelta",
}

build_options = {
    "replace_paths": [("*", "")],
    "excludes": ["tkinter", "unittest"],
    "zip_include_packages": ["encodings", "PySide6", "shiboken6"],
    "includes": [],
    "include_path": "./src",
    "build_exe": DIST_FOLDER,
}

executables = [
    Executable(
        "./src/main.py",
        base="gui",
        target_name="DIP.exe",
        icon="./res/icons/icon.ico",
        copyright=LICENSE,
    ),
    Executable(
        "./src/main.py",
        base="console",
        target_name="DIP_cli.exe",
        icon="./res/icons/icon.ico",
        copyright=LICENSE,
    ),
]

if DIST_FOLDER.is_dir():
    shutil.rmtree(DIST_FOLDER)
    print("Deleted dist folder.")

setup(
    name=APPNAME,
    version=VERSION,
    description=APPNAME,
    author=AUTHOR,
    license=LICENSE,
    options={"build_exe": build_options},
    executables=executables,
)

print(f"Copying {len(ADDITIONAL_ITEMS)} additional item(s)...")
for item, dest in ADDITIONAL_ITEMS.items():
    if item.is_dir():
        shutil.copytree(item, dest, dirs_exist_ok=True, copy_function=os.link)
    elif item.is_file():
        os.makedirs(dest.parent, exist_ok=True)
        os.link(item, dest)
    else:
        print(f"{str(item)!r} does not exist!")
        continue

    print(f"Copied {str(item)!r} to {str(dest.relative_to(DIST_FOLDER))!r}.")

for item in OBSOLETE_ITEMS:
    if item.is_file():
        os.remove(item)
    elif item.is_dir():
        shutil.rmtree(item)

    print(f"Removed item {str(item.relative_to(DIST_FOLDER))!r} from dist folder.")

print("Packing with FOMOD...")
if OUTPUT_FOLDER.is_dir():
    shutil.rmtree(OUTPUT_FOLDER)
    print("Deleted already existing output folder.")

print("Copying FOMOD...")
shutil.copytree(FOMOD_FOLDER, OUTPUT_FOLDER, dirs_exist_ok=True)

print("Copying DIP...")
shutil.copytree(DIST_FOLDER, OUTPUT_FOLDER / "DIP", dirs_exist_ok=True)

print("Packing into 7-zip archive...")
if Path(f"DIP_v{VERSION}.7z").is_file():
    os.remove(f"DIP_v{VERSION}.7z")
    print("Deleted already existing 7-zip archive.")

cmd = f"res\\7-zip\\7z.exe \
a \
DIP_v{VERSION}.7z \
{OUTPUT_FOLDER}"
os.system(cmd)

print("Done!")
