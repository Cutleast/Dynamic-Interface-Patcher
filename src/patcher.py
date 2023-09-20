"""
Part of Dynamic Interface Patcher (DIP).
Contains Patcher class.

Licensed under Attribution-NonCommercial-NoDerivatives 4.0 International
"""

import logging
import os
import shutil
import tempfile as tmp
import xml.etree.ElementTree as ET
from pathlib import Path

import jstyleson as json
import bsa_extractor as bsa

import ffdec
import utils
from main import MainApp


class Patcher:
    """
    Class for Patcher.
    """

    patch_data: dict[Path, dict] = None
    patch_path: Path = None
    shape_path: Path = None
    original_mod_path: Path = None
    ffdec_interface: ffdec.FFDec = None
    patch_dir: Path = None
    tmpdir: Path = None
    swf_files: dict[Path, Path] = None

    def __init__(self, app: MainApp, patch_path: Path, original_mod_path: Path):
        self.app = app
        self.patch_path = patch_path / "Patch"
        self.shape_path = patch_path / "Shapes"
        self.original_mod_path = original_mod_path

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

            shapes: dict[Path, list[int]] = {}
            for shape_data in patch_data.get("shapes", []):
                shape_path: Path = (self.shape_path / shape_data["fileName"]).resolve()

                if not shape_path.is_file():
                    self.log.error(
                        f"Failed to patch shape with id '{shape_data['id']}': \
File '{shape_path}' does not exist!"
                    )
                    continue

                shape_ids: list[int] = [
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
            mod_file = mod_file.with_suffix(".swf")

            if bsa_file:
                bsa_file = self.original_mod_path / bsa_file.name
            else:
                mod_file = mod_file.relative_to(self.patch_path)

            origin_path = self.original_mod_path / mod_file
            dest_path = self.tmpdir / mod_file
            if bsa_file is None:
                os.makedirs(dest_path.parent, exist_ok=True)
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

            data = utils.process_patch_data(patch_data)

            if self.app.debug:
                _debug_json = (Path(".") / f"{xml_file.stem}.json").resolve()
                with open(_debug_json, "w", encoding="utf8") as file:
                    file.write(json.dumps(data, indent=4))

            xml_root = self.split_frames(xml_root)

            for item in data:
                filter = item.get("filter", "")
                changes = item.get("changes", {})
                filter = f".{filter}"
                elements = xml_root.findall(filter)
                if not elements:
                    parent_filter, new_element_tag = filter.rsplit("/", 1)
                    self.log.debug(f"Creating new '{new_element_tag}' element at '{parent_filter}'...")
                    new_element = ET.Element(new_element_tag)
                    new_element.attrib = changes
                    parents = xml_root.findall(parent_filter)
                    for parent in parents:
                        parent.append(new_element)

                for element in elements:
                    for key, value in changes.items():
                        element.attrib[key] = str(value)
            patch_data = {}

            xml_root = self.unsplit_frames(xml_root)

            self.log.info("Writing XML file...")
            with open(xml_file, "wb") as file:
                xml_data.write(file, encoding="utf8")

            # Optional debug XML file
            if self.app.debug:
                _debug_xml = (Path(".") / f"{xml_file.name}").resolve()
                with open(_debug_xml, "w", encoding="utf8") as file:
                    file.write(utils.beautify_xml(
                        ET.tostring(xml_data.getroot(), encoding="utf8")
                    ))
                self.log.debug(f"Debug written to '{_debug_xml}'.")

    @staticmethod
    def split_frames(xml_element: ET.Element):
        """
        Split frames in xml_element recursively
        and return xml_element with frames.
        """

        new_frame = ET.Element("frame")
        current_frame = 1
        new_frame.set("frameId", str(current_frame))
        new_frame_subtags = ET.Element("subTags")
        new_frame.append(new_frame_subtags)

        frame_delimiters = xml_element.findall("./item[@type='ShowFrameTag']")

        # Iterate over all child elements
        for child in xml_element.findall("./"):
            # Split child recursively
            child = Patcher.split_frames(child)

            # If child is not a frame delimiter
            if len(frame_delimiters) > 1:
                # Remove child from xml_element
                xml_element.remove(child)

                # If child is not a frame delimiter
                if child.get("type") != "ShowFrameTag":
                    # Append child to current frame
                    new_frame_subtags.append(child)

                # If child is a frame delimiter
                elif child in frame_delimiters:
                    xml_element.append(new_frame)
                    # Create new frame
                    new_frame = ET.Element("frame")
                    current_frame += 1
                    new_frame.set("frameId", str(current_frame))
                    new_frame_subtags = ET.Element("subTags")
                    new_frame.append(new_frame_subtags)

        return xml_element

    @staticmethod
    def unsplit_frames(xml_element: ET.Element):
        """
        This functions is a reverse of split_frames.
        """

        for child in xml_element.findall("./"):
            frames = child.findall("./frame")

            for frame in frames:
                child.remove(frame)

                for frame_child in frame.findall("./subTags/"):
                    child.append(frame_child)
                
                frame_tag = ET.Element("item")
                frame_tag.set("type", "ShowFrameTag")
                child.append(frame_tag)

            Patcher.unsplit_frames(child)

        return xml_element

    
    def finish_patching(self):
        output_path = Path(os.getcwd()).parent

        # os.makedirs(output_path.parent, exist_ok=True)
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
