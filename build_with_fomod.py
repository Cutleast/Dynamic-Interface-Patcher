"""
This script builds the DIP.exe and packs
all its dependencies with a FOMOD in one folder
for installation as a mod.
"""

import shutil
import os
from pathlib import Path

COMPILER = "cx_freeze"  # "cx_freeze" or nuitka

DIST_FOLDER = Path("main.dist").resolve()
FOMOD_FOLDER = Path("fomod").resolve()
OUTPUT_FOLDER = Path("DIP_with_fomod").resolve() / "fomod"
APPNAME="Dynamic Interface Patcher"
VERSION="2.0.3"
AUTHOR="Cutleast"
LICENSE="Attribution-NonCommercial-NoDerivatives 4.0 International"
CONSOLE_MODE = "attach"  # "attach": Attaches to console it was started with (if any), "force": starts own console window, "disable": disables console completely
UNUSED_FILES = [
    DIST_FOLDER / "qt6datavisualization.dll",
    DIST_FOLDER / "qt6network.dll",
    DIST_FOLDER / "qt6pdf.dll",
    DIST_FOLDER / "PySide6" / "QtNetwork.pyd",
    DIST_FOLDER / "PySide6" / "QtDataVisualization.pyd",
    DIST_FOLDER / "libcrypto-1_1.dll",
    DIST_FOLDER / "assets" / "titlebar_icon.ico",
    DIST_FOLDER / "assets" / "new_icon.ico",
]
ADDITIONAL_ITEMS: dict[Path, Path] = {
    Path("src") / "assets": DIST_FOLDER / "assets",
}

print(f"Building with {COMPILER}...")
if COMPILER == "nuitka":
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
elif COMPILER == "cx_freeze":
    from cx_Freeze import setup, Executable
    import sys

    build_options = {
        "replace_paths": [("*", "")],
        "excludes": [],
        "include_path": "./src",
        "build_exe": DIST_FOLDER.name,
    }

    executables = [
        Executable(
            "./src/main.py",
            base="gui",
            target_name="DIP.exe",
            icon="./src/assets/icon.ico",
            copyright=LICENSE,
        ),
        Executable(
            "./src/main.py",
            base="console",
            target_name="DIP_cli.exe",
            icon="./src/assets/icon.ico",
            copyright=LICENSE,
        )
    ]

    sys.argv.append("build_exe")

    setup(
        name=APPNAME,
        version=VERSION,
        description=APPNAME,
        author=AUTHOR,
        license=LICENSE,
        options={"build_exe": build_options},
        executables=executables,
    )

else:
    raise ValueError(f"Compiler {COMPILER!r} not supported!")

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
if Path(f"DIP_v{VERSION}.7z").is_file():
    os.remove(f"DIP_v{VERSION}.7z")
    print("Deleted already existing 7-zip archive.")

cmd = f'7-zip\\7z.exe \
a \
DIP_v{VERSION}.7z \
{OUTPUT_FOLDER}'
os.system(cmd)

print("Done!")
