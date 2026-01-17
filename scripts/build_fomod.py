"""
Copyright (c) Cutleast

Script that bundles the DIP build with the FOMOD and packs it into a 7z file.
"""

import logging
import os
import shutil
from pathlib import Path
from xml.etree import ElementTree as ET

from cutleast_core_lib.builder.build_metadata import BuildMetadata
from cutleast_core_lib.core.utilities.process_runner import run_process

DIST_PATH = Path("dist") / "DIP"
FOMOD_PATH = Path("fomod")
OUTPUT_PATH = Path("dist") / "fomod"
METADATA: BuildMetadata = BuildMetadata.from_pyproject(Path("pyproject.toml"))
OUTPUT_ARCHIVE_PATH = (
    Path("dist") / f"{METADATA.display_name}_v{METADATA.project_version}_fomod.7z"
)

logging.basicConfig(level=logging.DEBUG)


def update_fomod_version(info_xml_path: Path, new_version: str) -> None:
    if not info_xml_path.is_file():
        logging.error(f"The file '{info_xml_path}' does not exist!")
        return

    try:
        tree = ET.parse(info_xml_path)
        root = tree.getroot()

        version_element = root.find(".//Version")
        if version_element is None:
            logging.error(f"Found no <Version> element in '{info_xml_path}'.")
            return

        version_element.text = new_version
        tree.write(info_xml_path, encoding="utf-8", xml_declaration=True)

        logging.info(f"Updated version in '{info_xml_path}' to {new_version}.")
    except ET.ParseError as ex:
        logging.error(f"Failed to parse '{info_xml_path}': {ex}", exc_info=ex)


def prepare_fomod() -> None:
    logging.info("Preparing FOMOD...")

    if OUTPUT_PATH.is_dir():
        shutil.rmtree(OUTPUT_PATH)
        logging.info("Deleted already existing output directory.")

    logging.info(f"Copying FOMOD to '{OUTPUT_PATH}'...")
    shutil.copytree(FOMOD_PATH, OUTPUT_PATH)

    logging.info("Updating the FOMOD's version...")
    update_fomod_version(OUTPUT_PATH / "info.xml", str(METADATA.project_version))


def build() -> None:
    prepare_fomod()

    logging.info(f"Copying '{DIST_PATH}' to '{OUTPUT_PATH}'...")
    shutil.copytree(DIST_PATH, OUTPUT_PATH / "DIP", copy_function=os.link)

    logging.info("Packing into 7-zip archive...")
    if OUTPUT_ARCHIVE_PATH.is_file():
        os.unlink(OUTPUT_ARCHIVE_PATH)
        logging.info("Deleted already existing 7-zip archive.")

    cmd: list[str] = [
        "..\\res\\7-zip\\7z.exe",
        "a",
        str(OUTPUT_ARCHIVE_PATH.relative_to(DIST_PATH.parent)),
        str(OUTPUT_PATH.relative_to(DIST_PATH.parent)),
    ]
    cwd: str = os.getcwd()
    os.chdir(DIST_PATH.parent)
    run_process(cmd, live_output=True)
    os.chdir(cwd)

    logging.info(f"Packed into '{OUTPUT_ARCHIVE_PATH}'.")


if __name__ == "__main__":
    try:
        build()
    except Exception as ex:
        logging.error(f"Failed to build FOMOD: {ex}", exc_info=ex)

        shutil.rmtree(OUTPUT_PATH, ignore_errors=True)
