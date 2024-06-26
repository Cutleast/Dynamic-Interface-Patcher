"""
This script builds the DIP.exe and packs
all its dependencies with a FOMOD in one folder
for installation as a mod.
"""

import shutil
import os
from pathlib import Path

DIST_FOLDER = Path("main.dist").resolve()
FOMOD_FOLDER = Path("fomod").resolve()
OUTPUT_FOLDER = Path("DIP_with_fomod").resolve() / "fomod"
APPNAME="Dynamic Interface Patcher"
VERSION="2.0.0"
AUTHOR="Cutleast"
LICENSE="Attribution-NonCommercial-NoDerivatives 4.0 International"
CONSOLE_MODE = "attach"  # "attach": Attaches to console it was started with (if any), "force": starts own console window, "disable": disables console completely
UNUSED_FILES = [
    DIST_FOLDER / "qt6datavisualization.dll",
    DIST_FOLDER / "qt6network.dll",
    DIST_FOLDER / "qt6pdf.dll",
    DIST_FOLDER / "PySide6" / "QtNetwork.pyd",
    DIST_FOLDER / "PySide6" / "QtDataVisualization.pyd",
    DIST_FOLDER / "libcrypto-1_1.dll"
]

print("Building with nuitka...")
cmd = f'nuitka \
--msvc="latest" \
--standalone \
--windows-console-mode={CONSOLE_MODE} \
--include-data-dir="./src/assets=./assets" \
--enable-plugin=pyside6 \
--remove-output \
--company-name="{AUTHOR}" \
--product-name="{APPNAME}" \
--file-version="{VERSION}" \
--product-version="{VERSION}" \
--file-description="{APPNAME}" \
--copyright="{LICENSE}" \
--nofollow-import-to=tkinter \
--windows-icon-from-ico="./src/assets/icon.ico" \
--output-filename="DIP.exe" \
"./src/main.py"'
os.system(cmd)

print("Deleting unused files...")
for file in UNUSED_FILES:
    if not file.is_file():
        continue
    os.remove(file)
    print(f"Removed '{file.name}'.")

print("Packing with FOMOD...")
if OUTPUT_FOLDER.is_dir():
    shutil.rmtree(OUTPUT_FOLDER)
    print("Deleted already existing output folder.")

print("Copying FOMOD...")
shutil.copytree(FOMOD_FOLDER, OUTPUT_FOLDER, dirs_exist_ok=True)

print("Copying DIP...")
shutil.copytree(DIST_FOLDER, OUTPUT_FOLDER / "DIP", dirs_exist_ok=True)

print("Copying 7-zip files...")
shutil.copytree("./7-zip", OUTPUT_FOLDER / "DIP", dirs_exist_ok=True)

print("Packing into 7-zip archive...")
cmd = f'7-zip\\7z.exe \
a \
DIP_v{VERSION}.7z \
{OUTPUT_FOLDER}'
os.system(cmd)

print("Done!")
