"""
Copyright (c) Cutleast
"""

import os
import shutil
from pathlib import Path

import pyinstaller_versionfile

# Application details
APPNAME = "Dynamic Interface Patcher"
VERSION = "2.1.3"
AUTHOR = "Cutleast"
LICENSE = "Attribution-NonCommercial-NoDerivatives 4.0 International"
DIST_FOLDER = Path("dist").resolve()
BUILD_FOLDER = Path("build").resolve()
FOMOD_FOLDER = Path("fomod").resolve()
OUTPUT_FOLDER = Path("DIP_with_fomod").resolve() / "fomod"
OBSOLETE_ITEMS: list[Path] = []
ADDITIONAL_ITEMS: dict[Path, Path] = {
    Path("res") / "7-zip": OUTPUT_FOLDER / "DIP" / "7-zip",
    Path("res") / "ffdec": OUTPUT_FOLDER / "DIP" / "ffdec",
    Path("res") / "jre.7z": OUTPUT_FOLDER / "DIP" / "jre.7z",
    Path("res") / "xdelta": OUTPUT_FOLDER / "DIP" / "xdelta",
}

for folder in [DIST_FOLDER, BUILD_FOLDER]:
    if folder.is_dir():
        shutil.rmtree(folder)
        print(f"Deleted {folder} folder.")

print("Creating version.txt...")
pyinstaller_versionfile.create_versionfile_from_input_file(
    output_file="version.txt",
    input_file="version.yml",
    version=VERSION,
)

print("Building Executables with PyInstaller...")
os.system(
    f"pyinstaller " "--noconfirm " "--clean " f"--distpath {DIST_FOLDER} " "DIP.spec"
)

print("Packing with FOMOD...")
if OUTPUT_FOLDER.is_dir():
    shutil.rmtree(OUTPUT_FOLDER)
    print("Deleted already existing output folder.")

print("Copying FOMOD...")
shutil.copytree(FOMOD_FOLDER, OUTPUT_FOLDER, dirs_exist_ok=True)

print("Copying DIP...")
shutil.copytree(DIST_FOLDER / "DIP", OUTPUT_FOLDER / "DIP", dirs_exist_ok=True)

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
    print(f"Copied {str(item)!r} to {str(dest.relative_to(OUTPUT_FOLDER))!r}.")

for item in OBSOLETE_ITEMS:
    if item.is_file():
        os.remove(item)
    elif item.is_dir():
        shutil.rmtree(item)
    print(f"Removed item {str(item.relative_to(OUTPUT_FOLDER))!r} from dist folder.")

# Update version in info.xml
info_xml_path = OUTPUT_FOLDER / "info.xml"
if info_xml_path.is_file():
    with info_xml_path.open("r", encoding="utf-16") as file:
        lines = file.readlines()
    with info_xml_path.open("w", encoding="utf-16") as file:
        for line in lines:
            if "<Version>" in line:
                line = f"\t<Version>{VERSION}</Version>\n"
            file.write(line)
    print(f"Updated version in {info_xml_path} to {VERSION}.")

print("Packing into 7-zip archive...")
if Path(f"DIP_v{VERSION}.7z").is_file():
    os.remove(f"DIP_v{VERSION}.7z")
    print("Deleted already existing 7-zip archive.")

cmd = f"res\\7-zip\\7z.exe a DIP_v{VERSION}.7z {OUTPUT_FOLDER}"
os.system(cmd)

print("Done!")
