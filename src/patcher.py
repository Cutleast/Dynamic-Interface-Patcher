"""
Part of Dynamic Interface Patcher (DIP).
Contains Patcher class.

Licensed under Attribution-NonCommercial-NoDerivatives 4.0 International
"""


import html
import logging
import os
import re
import shutil
import tempfile as tmp
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List

import jstyleson as json
import bsa_extractor as bsa

import errors
import ffdec
import utils
from main import MainApp


class Patcher:
    """
    Class for Patcher.
    """

    patch_data: Dict[Path, dict] = None
    patch_path: Path = None
    shape_path: Path = None
    original_mod_path: Path = None
    ffdec_interface: ffdec.FFDec = None
    patch_dir: Path = None
    tmpdir: Path = None
    swf_files: Dict[Path, Path] = None

    def __init__(self, app: MainApp, patch_path: Path, racemenu_path: Path):
        self.app = app
        self.patch_path = patch_path / "Patch"
        self.shape_path = patch_path / "Shapes"
        self.original_mod_path = racemenu_path

        self.log = logging.getLogger(self.__repr__())
        self.log.addHandler(self.app.log_str)
        self.log.setLevel(self.app.log.level)

        self.load_patch_data()

    def __repr__(self):
        return "Patcher"

    def load_patch_data(self):
        self.patch_data = {}

        self.log.info("Loading patch files...")

        # Scan for json files
        for json_file in self.patch_path.glob("**\\*.json"):
            self.patch_data[json_file] = json.loads(
                json_file.read_text(encoding="utf8")
            )
            json_file = json_file.relative_to(self.patch_path)
            self.log.debug(f"Loaded '{json_file}'.")

        self.log.info(f"Loaded {len(self.patch_data)} patch files.")

    def patch_shapes(self):
        for patch_file, patch_data in self.patch_data.items():
            swf_file = self.swf_files[patch_file]

            shapes: Dict[Path, List[int]] = {}
            for shape_data in patch_data.get("shapes", []):
                shape_path: Path = (self.shape_path / shape_data["fileName"]).resolve()

                if not shape_path.is_file():
                    self.log.error(
                        f"Failed to patch shape with id '{shape_data['id']}': \
File '{shape_path}' does not exist!"
                    )
                    continue

                shape_ids: List[int] = [
                    int(shape_id)
                    for shape_id in shape_data["id"].split(",")
                ]

                if shape_path in shapes:
                    shapes[shape_path] += shape_ids
                else:
                    shapes[shape_path] = shape_ids

            if shapes:
                # Initialize ffdec interface if required
                if self.ffdec_interface is None:
                    self.ffdec_interface = ffdec.FFDec(swf_file, self.app)
                else:
                    self.ffdec_interface.swf_path = swf_file

                self.ffdec_interface.replace_shapes(shapes)

    def copy_files(self):
        """
        Copies all required files to patch to the temp folder.
        """

        self.log.info("Copying mod files...")

        self.swf_files = {}

        for file in self.patch_data.keys():
            bsa_file, mod_file = utils.parse_path(file)

            if bsa_file:
                bsa_file = self.original_mod_path / bsa_file.name

            mod_file = mod_file.with_suffix(".swf")
            origin_path = self.original_mod_path / mod_file
            dest_path = self.tmpdir / mod_file
            if bsa_file is None:
                shutil.copyfile(origin_path, dest_path)
            else:
                bsa_archive = bsa.BSAArchive.parse_file(str(bsa_file))
                bsa_archive.extract_file(to_dir=self.tmpdir, file=mod_file)
            self.swf_files[file] = dest_path

        self.log.info("Mod files ready to patch.")

    def convert_swfs2xmls(self):
        for swf_file in self.swf_files.values():
            self.log.info(f"Converting '{swf_file}'...")

            # Initialize ffdec interface if required
            if self.ffdec_interface is None:
                self.ffdec_interface = ffdec.FFDec(swf_file, self.app)
            else:
                self.ffdec_interface.swf_path = swf_file

            self.ffdec_interface.swf2xml()

    def convert_xmls2swfs(self):
        for swf_file in self.swf_files.values():
            xml_file = swf_file.with_suffix(".xml")

            # Initialize ffdec interface if required
            if self.ffdec_interface is None:
                self.ffdec_interface = ffdec.FFDec(swf_file, self.app)
            else:
                self.ffdec_interface.swf_path = swf_file
            
            self.ffdec_interface.xml2swf(xml_file)

    def patch_xmls(self):
        for key, value in self.patch_data.items():
            patch_file = key
            patch_data = value.get("swf")
            if not patch_data:
                continue

            swf_file = self.swf_files[patch_file]
            xml_file = swf_file.with_suffix(".xml")

            self.log.info(f"Patching '{xml_file.name}'...")

            xml_data = ET.parse(str(xml_file))
            xml_root = xml_data.getroot()

            data = utils.process_patch_data(patch_data, pre_result={}, pre_filters="", pre_changes={})

            for filter, changes in data.items():
                filter = f".{filter}"
                elements = xml_root.findall(filter)
                if not elements:
                    self.log.debug(f"Failed to patch element! Found no matching element for filter '{filter}'.")
                for element in elements:
                    for key, value in changes.items():
                        element.attrib[key] = str(value)
            patch_data = {}

            self.log.info("Writing XML file...")
            with open(xml_file, "wb") as file:
                xml_data.write(file, encoding="utf8")

            # Optional debug XML file
            _debug_xml = (Path(".") / f"{xml_file.name}").resolve()
            with open(_debug_xml, "wb") as file:
                xml_data.write(file, encoding="utf8")
            self.log.debug(f"Debug written to '{_debug_xml}'.")

    def finish_patching(self):
        output_path = Path(".").resolve().parent
        
        os.makedirs(output_path.parent, exist_ok=True)
        for file in self.swf_files.values():
            dest = output_path / file.relative_to(self.tmpdir)
            os.makedirs(dest.parent, exist_ok=True)
            if dest.is_file():
                os.remove(dest)
            shutil.copyfile(file, dest)
        self.log.info(f"Output written to '{output_path}'.")

    def patch(self):
        """
        Patches mod through following process:
            1. Copy original mod to a temp folder.
            1.1 Extract BSAs if required.
            2. Patch shapes.
            3. Convert SWFs to XMLs.
            4. Patch XMLs.
            5. Convert XMLs back to SWFs.
            6. Copy patched mod back to current directory.
        """

        self.log.info("Patching mod...")

        # 0. Create Temp folder
        with tmp.TemporaryDirectory(prefix="DIP_") as tmpdir:
            self.tmpdir = Path(tmpdir).resolve()

            self.log.debug(f"Created temporary folder at '{self.tmpdir}'.")

            # 1. Copy original mod files to patch
            # 1.1 and extract BSAs if required
            self.copy_files()

            # 2. Patch shapes
            self.patch_shapes()

            # 3. Convert SWFs to XMLs
            self.convert_swfs2xmls()

            # 4. Patch XMLs
            self.patch_xmls()

            # 5. Convert XMLs back to SWFs
            self.convert_xmls2swfs()

            # 6. Copy patched files back to current directory
            self.finish_patching()
        
        # Send done signal to app
        self.log.info("Patch complete!")
        self.app.done_signal.emit()
