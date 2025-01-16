"""
Copyright (c) Cutleast
"""

import logging
import os
import shutil
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Optional

import jstyleson as json
from PySide6.QtWidgets import QApplication

from core.archive.archive import Archive
from core.bsa import BSAArchive
from core.config.config import Config
from core.utilities.filesystem import is_dir, is_file
from core.utilities.glob import glob
from core.utilities.path_splitter import split_path_with_bsa
from core.utilities.xml_utils import beautify_xml, split_frames, unsplit_frames

from .ffdec import FFDecInterface
from .xdelta import XDeltaInterface


class Patcher:
    """
    Class for Patcher.
    """

    log: logging.Logger = logging.getLogger("Patcher")

    config: Config
    app_path: Path
    cwd_path: Path

    jre_archive_path: Path
    patch_data: dict[Path, dict]
    patch_path: Path
    shape_path: Path
    original_mod_path: Path
    ffdec_interface: FFDecInterface
    xdelta_interface: XDeltaInterface
    patch_dir: Path
    swf_files: dict[Path, Path]
    tmp_path: Optional[Path] = None

    def __init__(self):
        self.config = QApplication.instance().config
        self.app_path = QApplication.instance().app_path
        self.cwd_path = QApplication.instance().cwd_path

        self.jre_archive_path = self.app_path / "jre.7z"

        self.ffdec_interface = FFDecInterface()
        self.xdelta_interface = XDeltaInterface()

    def load_patch_data(self) -> None:
        self.patch_data = {}

        self.log.info(f"Loading patch files from {str(self.patch_path)!r}...")

        # Scan for json files
        for json_file in glob(self.patch_path, "*.json"):
            self.patch_data[json_file] = json.loads(
                json_file.read_text(encoding="utf8")
            )
            json_file = json_file.relative_to(self.patch_path)
            self.log.debug(f"Loaded '{json_file}'.")

        # Scan for binary files
        for bin_file in glob(self.patch_path, "*.bin"):
            self.patch_data[bin_file] = None
            bin_file = bin_file.relative_to(self.patch_path)
            self.log.debug(f"Found binary patch '{bin_file}'.")

        self.log.info(f"Loaded {len(self.patch_data)} patch files.")

    def patch_shapes(self):
        for patch_file, patch_data in self.patch_data.items():
            if patch_data is None:
                continue

            swf_file = self.swf_files[patch_file]

            shapes: dict[Path, list[int]] = {}
            for shape_data in patch_data.get("shapes", []):
                shape_path: Path = (self.shape_path / shape_data["fileName"]).resolve()

                if not is_file(shape_path):
                    self.log.error(
                        f"Failed to patch shape with id '{shape_data['id']}': "
                        f"File '{shape_path}' does not exist!"
                    )
                    continue

                shape_ids: list[int] = [
                    int(shape_id) for shape_id in shape_data["id"].split(",")
                ]

                if shape_path in shapes:
                    shapes[shape_path] += shape_ids
                else:
                    shapes[shape_path] = shape_ids

            if shapes:
                self.ffdec_interface.replace_shapes(swf_file, shapes)

    def copy_files(self):
        """
        Copies all required files to patch to the temp folder.
        """

        self.log.info("Copying mod files...")

        self.swf_files = {}

        file: Path
        bsa_file: Optional[Path]
        mod_file: Path
        for file in list(self.patch_data.keys()):
            bsa_file, mod_file = split_path_with_bsa(file)
            mod_file = mod_file.with_suffix(".swf")

            if bsa_file:
                bsa_file = self.original_mod_path / bsa_file.name
            else:
                mod_file = mod_file.relative_to(self.patch_path)

            origin_path = self.original_mod_path / mod_file

            dest_path = self.get_tmp_dir() / mod_file
            if bsa_file is None:
                if is_file(origin_path):
                    os.makedirs(dest_path.parent, exist_ok=True)
                    shutil.copyfile(origin_path, dest_path)

                # Skip missing SWF files
                else:
                    self.log.warning(
                        f"{str(origin_path)!r} does not exist! Skipped patch file."
                    )
                    self.patch_data.pop(file)
                    continue
            elif is_file(bsa_file):
                bsa_archive = BSAArchive(bsa_file)
                bsa_archive.extract_file(mod_file, self.get_tmp_dir())

            # Skip missing BSA files
            else:
                self.log.warning(
                    f"{str(bsa_file)!r} does not exist! Skipped patch file."
                )
                self.patch_data.pop(file)
                continue

            self.swf_files[file] = dest_path

        self.log.info("Mod files ready to patch.")

    def convert_swfs2xmls(self):
        for patch_file, swf_file in self.swf_files.items():
            if patch_file.suffix != ".bin":
                self.ffdec_interface.swf2xml(swf_file)

    def convert_xmls2swfs(self):
        for patch_file, swf_file in self.swf_files.items():
            if patch_file.suffix != ".bin":
                xml_file = swf_file.with_suffix(".xml")
                self.ffdec_interface.xml2swf(xml_file)

    def patch_xmls(self):
        for key, value in self.patch_data.items():
            patch_file: Path = key

            if value is None:
                continue

            patch_data: dict | None = value.get("swf")
            if not patch_data:
                continue

            # Skip missing SWF files
            if patch_file not in self.swf_files:
                continue

            swf_file = self.swf_files[patch_file]
            xml_file = swf_file.with_suffix(".xml")

            self.log.info(f"Patching '{xml_file.name}'...")

            xml_data = ET.parse(str(xml_file))
            xml_root = xml_data.getroot()

            data = Patcher.process_patch_data(patch_data)

            if self.config.debug_mode:
                _debug_json = (Path(".") / f"{xml_file.stem}.json").resolve()
                with open(_debug_json, "w", encoding="utf8") as file:
                    file.write(json.dumps(data, indent=4))

            xml_root = split_frames(xml_root)

            for item in data:
                filter = item.get("filter", "")
                changes = item.get("changes", {})
                filter = f".{filter}"
                elements = xml_root.findall(filter)
                if not elements:
                    # TODO: Fix filter appearing in new_element_tag
                    parent_filter, new_element_tag = filter.rsplit("/", 1)
                    self.log.debug(
                        f"Creating new '{new_element_tag}' element at '{parent_filter}'..."
                    )
                    new_element = ET.Element(new_element_tag)
                    new_element.attrib = changes
                    parents = xml_root.findall(parent_filter)
                    for parent in parents:
                        parent.append(new_element)

                for element in elements:
                    for key, value in changes.items():
                        element.attrib[key] = str(value)
            patch_data = {}

            xml_root = unsplit_frames(xml_root)

            self.log.info("Writing XML file...")
            with open(xml_file, "wb") as file:
                xml_data.write(file, encoding="utf8")

            # Optional debug XML file
            if self.config.debug_mode:
                _debug_xml = (Path(".") / f"{xml_file.name}").resolve()
                with open(_debug_xml, "w", encoding="utf8") as file:
                    file.write(
                        beautify_xml(
                            ET.tostring(xml_data.getroot(), encoding="unicode")
                        )
                    )
                self.log.debug(f"Debug written to '{_debug_xml}'.")

    def repack_bsas(self, output_folder: Path):
        """
        Repacks BSAs with patched files at `output_folder`.
        """

        bsa_archives: dict[Path, list[Path]] = {}
        """
        Stores path to BSAs with list of patched files.
        """

        os.makedirs(output_folder, exist_ok=True)

        for file in self.patch_data.keys():
            bsa_file, mod_file = split_path_with_bsa(file)
            patched_file = mod_file.with_suffix(".swf")

            # Skip missing SWF files
            if not is_file(self.get_tmp_dir() / patched_file):
                self.log.warning(
                    f"Skipped missing patched file {str(self.get_tmp_dir() / patched_file)!r}."
                )
                continue

            if bsa_file:
                bsa_file = self.original_mod_path / bsa_file.name

                if bsa_file in bsa_archives:
                    bsa_archives[bsa_file].append(patched_file)
                else:
                    bsa_archives[bsa_file] = [patched_file]
            else:
                src = self.get_tmp_dir() / file
                dst = output_folder / file

                # Backup original file
                if is_file(dst):
                    os.rename(
                        dst,
                        dst.with_suffix(
                            dst.suffix + time.strftime(".%d-%m-%Y-%H-%M-%S")
                        ),
                    )

                shutil.copyfile(src, dst)

        for bsa_file, files in bsa_archives.items():
            self.log.info(f"Repacking {bsa_file.name!r} with patched files...")

            # 1. Extract BSA to a new temp folder
            bsa_archive = BSAArchive(bsa_file)
            os.mkdir(self.get_tmp_dir() / bsa_file.name)
            bsa_archive.extract(self.get_tmp_dir() / bsa_file.name)

            # 2. Copy patched files over original files
            for file in files:
                src = self.get_tmp_dir() / file
                dst = self.get_tmp_dir() / bsa_file.name / file

                # Remove original file from BSA
                if is_file(dst):
                    os.remove(dst)

                shutil.copyfile(src, dst)

            # 3. Repack BSA at output folder
            dst = output_folder / bsa_file.name

            # Backup original BSA
            if is_file(dst):
                os.rename(
                    dst,
                    dst.with_suffix(dst.suffix + time.strftime(".%d-%m-%Y-%H-%M-%S")),
                )

            BSAArchive.create_archive(
                self.get_tmp_dir() / bsa_file.name, output_folder / bsa_file.name
            )

    def finish_patching(self) -> None:
        output_path: Path
        if self.config.output_folder is not None:
            output_path = self.config.output_folder
        else:
            output_path = self.cwd_path.parent

        if self.config.repack_bsas:
            self.repack_bsas(output_path)
        else:
            for file in self.swf_files.values():
                dest = output_path / file.relative_to(self.get_tmp_dir())
                os.makedirs(dest.parent, exist_ok=True)

                # Backup already existing file
                if is_file(dest):
                    shutil.move(
                        dest,
                        dest.with_suffix(
                            dest.suffix + time.strftime(".%d-%m-%Y-%H-%M-%S")
                        ),
                    )

                shutil.copyfile(file, dest)
                self.log.debug(f"Copied {str(file)!r} to {str(dest)!r}.")

        self.log.info(f"Output written to '{output_path}'.")

    def setup_jre(self):
        """
        Extracts Java Runtime from jre.7z and redirects FFDec to it.
        """

        self.log.info("Extracting Java Runtime from jre.7z...")

        tmp_folder = self.get_tmp_dir()

        archive: Archive = Archive.load_archive(self.jre_archive_path)

        if not archive.glob("*/bin/java.exe"):
            raise Exception("Archive does not contain a valid java.exe!")

        archive.extract_all(tmp_folder)
        java_path: Path = list(glob(tmp_folder, "java.exe"))[0]

        self.log.info(f"Java Runtime extracted to '{java_path}'.")
        self.log.info("Setting up FFDec...")

        # Write jre_path in ffdec.bat
        ffdec_bat_path = self.ffdec_interface.bin_path
        orig_bat_path = ffdec_bat_path.with_stem("ffdec_orig")

        text = orig_bat_path.read_text()
        lines = text.splitlines()
        last_line = lines[-1]

        last_line = last_line.replace("java", f'"{java_path}"', 1)
        lines[-1] = last_line

        ffdec_bat_path.write_text("\n".join(lines))

        self.log.info("FFDec setup complete.")

    def get_tmp_dir(self):
        if self.tmp_path is None:
            self.tmp_path = Path(tempfile.mkdtemp(prefix="DIP_"))
            self.log.debug(f"Created temporary directory at {str(self.tmp_path)!r}.")

        return self.tmp_path

    def apply_binary_patches(self) -> None:
        """
        Applies binary patches to original files.
        """

        binary_patches: list[Path] = [
            file for file in self.patch_data.keys() if file.suffix == ".bin"
        ]

        if not binary_patches:
            return

        self.log.info(f"Applying {len(binary_patches)} binary patch(es)...")

        for patch_file in binary_patches:
            swf_file: Path = self.swf_files[patch_file]

            self.xdelta_interface.patch_file(swf_file, patch_file)

        self.log.info("Binary patches applied.")

    def check_patch(self, folder: Path) -> bool:
        """
        Checks if a folder contains a valid patch.

        Args:
            folder (Path): Path to the folder to check.

        Returns:
            bool: True if the folder contains a valid patch, False otherwise.
        """

        patch_path: Path = folder / "Patch"

        if not is_dir(patch_path):
            return False

        if not list(glob(patch_path, "*.json")) and not list(glob(patch_path, "*.bin")):
            return False

        return True

    def patch(self, patch_path: Path, original_mod_path: Path) -> float:
        """
        Patches mod through following process:

        0. Load patch data
        1. Setup JRE if required
        2. Copy original mod files to patch and extract BSAs if required
        3. Patch shapes
        4. Convert SWFs to XMLs
        5. Patch XMLs
        6. Convert XMLs back to SWFs
        7. Apply binary patches with xdelta
        8. Copy patched files back to current directory and repack BSAs if enabled

        Args:
            patch_path: Path to the patch file.
            original_mod_path: Path to the original mod file.

        Returns:
            float: duration in seconds
        """

        self.patch_path = patch_path / "Patch"
        self.shape_path = patch_path / "Shapes"
        self.original_mod_path = original_mod_path

        self.log.info("Patching mod...")

        start_time: float = time.time()

        # 0. Load patch data
        self.load_patch_data()

        # 1. Setup JRE if required
        if any(
            file for file in self.patch_data.keys() if file.suffix.lower() == ".json"
        ):
            self.setup_jre()

        # 2. Copy original mod files to patch and extract BSAs if required
        self.copy_files()

        # 3. Patch shapes
        self.patch_shapes()

        # 4. Convert SWFs to XMLs
        self.convert_swfs2xmls()

        # 5. Patch XMLs
        self.patch_xmls()

        # 6. Convert XMLs back to SWFs
        self.convert_xmls2swfs()

        # 7. Apply binary patches with xdelta
        self.apply_binary_patches()

        # 8. Copy patched files back to current directory and repack BSAs if enabled
        self.finish_patching()

        duration: float = time.time() - start_time
        self.log.info(f"Patching complete in {duration:.3f} second(s).")

        return duration

    def clean(self) -> None:
        if self.tmp_path is not None and is_dir(self.tmp_path):
            shutil.rmtree(self.tmp_path, ignore_errors=True)
            self.tmp_path = None
            self.log.info("Removed temporary folder.")

    def get_patches(self) -> list[str]:
        """
        Returns a list of possible paths to patches.

        Returns:
            list[str]: List of possible paths to patches.
        """

        self.log.debug("Scanning for patches...")

        paths_to_scan: list[Path] = [
            self.cwd_path,
            self.cwd_path.parent,
        ]
        patches: list[str] = []

        for path in paths_to_scan:
            self.log.debug(f"Searching in '{path}'...")

            for item in path.iterdir():
                if not is_dir(item):
                    continue

                if item.match("*DIP*") and (item / "Patch").is_dir():
                    patches.append(str(item))

        self.log.debug(f"Found {len(patches)} patches.")

        return patches

    @staticmethod
    def process_patch_data(patch_data: dict) -> list[dict[str, str | dict]]:
        """
        Processes patch data.

        Args:
            patch_data (dict): Patch data to process.

        Returns:
            list[dict[str, str | dict]]: Processed patch data.
        """

        result: list[dict[str, str | dict]] = []

        def process_data(
            data: dict[str, Any] | list, cur_filter: str = ""
        ) -> dict[str, str | dict]:
            cur_result: dict[str, str | dict] = {}
            cur_changes: dict[str, str] = {}

            if isinstance(data, list):
                for item in data:
                    if child_result := process_data(item, cur_filter + "/item"):
                        result.append(child_result)

            else:
                for key, value in data.items():
                    if isinstance(value, str):
                        if key.startswith("#"):
                            attribute: str = key.removeprefix("#")
                            # Fix frames
                            if attribute == "frameId":
                                cur_filter, _ = cur_filter.rsplit("/", 1)
                                cur_filter += "/frame"
                            cur_filter += f"[@{attribute}='{value}']"
                        else:
                            attribute: str = key.removeprefix("~")
                            cur_changes[attribute] = value

                        if cur_filter and cur_changes:
                            cur_result = {"filter": cur_filter, "changes": cur_changes}
                    else:
                        if child_result := process_data(value, cur_filter + f"/{key}"):
                            result.append(child_result)

            return cur_result

        if cur_result := process_data(patch_data):
            result.append(cur_result)

        return result
