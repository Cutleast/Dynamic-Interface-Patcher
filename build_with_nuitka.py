"""
Copyright (c) Cutleast

Build script for nuitka. Run with `python nuitka.py`.
"""

import os
import shutil
from pathlib import Path
from xml.etree import ElementTree as ET

# Application details
APPNAME = "Dynamic Interface Patcher"
VERSION = "2.1.5-beta"
AUTHOR = "Cutleast"
LICENSE = "GNU General Public License v3.0"
DIST_FOLDER = Path("main.dist").resolve()
FOMOD_FOLDER = Path("fomod").resolve()
OUTPUT_FOLDER = Path("DIP_with_fomod").resolve() / "fomod"
OBSOLETE_ITEMS: list[Path] = [DIST_FOLDER / "lib" / "qtpy" / "tests"]
CONSOLE_MODE = "force"  # "attach": Attaches to console it was started with (if any), "force": starts own console window, "disable": disables console completely
ADDITIONAL_ITEMS: dict[Path, Path] = {
    Path("res") / "7-zip": DIST_FOLDER / "7-zip",
    Path("res") / "ffdec": DIST_FOLDER / "ffdec",
    Path("res") / "jre.7z": DIST_FOLDER / "jre.7z",
    Path("res") / "xdelta": DIST_FOLDER / "xdelta",
    Path("res") / "glob.dll": DIST_FOLDER / "glob.dll",
}

cmd = f'.venv\\scripts\\nuitka \
--msvc="latest" \
--standalone \
--windows-console-mode={CONSOLE_MODE} \
--enable-plugin=pyside6 \
--remove-output \
--company-name="{AUTHOR}" \
--product-name="{APPNAME}" \
--file-version="{VERSION.split("-")[0]}" \
--product-version="{VERSION.split("-")[0]}" \
--file-description="{APPNAME}" \
--copyright="{LICENSE}" \
--nofollow-import-to=tkinter \
--windows-icon-from-ico="./res/icons/icon.ico" \
--output-filename="DIP.exe" \
"./src/main.py"'

if DIST_FOLDER.is_dir():
    shutil.rmtree(DIST_FOLDER)
    print("Deleted dist folder.")

os.system(cmd)

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


def update_fomod_version(info_xml_path: Path, new_version: str) -> None:
    if not info_xml_path.is_file():
        print(f"The file {info_xml_path} does not exist!")
        return

    try:
        tree = ET.parse(info_xml_path)
        root = tree.getroot()

        version_element = root.find(".//Version")
        if version_element is None:
            print(f"Found no <Version> element in {info_xml_path}.")
            return

        version_element.text = new_version
        tree.write(info_xml_path, encoding="utf-8", xml_declaration=True)

        print(f"Updated version in {info_xml_path} to {new_version}.")
    except ET.ParseError as e:
        print(f"Failed to parse {info_xml_path}: {e}")


update_fomod_version(OUTPUT_FOLDER / "info.xml", VERSION)

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
