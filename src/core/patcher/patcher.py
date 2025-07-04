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
from typing import Optional

from sse_bsa import BSAArchive

from core.cli_interface.ffdec import FFDecInterface
from core.cli_interface.xdelta import XDeltaInterface
from core.config.config import Config
from core.patch.patch import Patch
from core.patch.patch_file import PatchFile
from core.patch.patch_item import PatchItem
from core.patch.patch_type import PatchType
from core.utilities.exe_info import get_current_path
from core.utilities.filesystem import is_dir, is_file, mkdir
from core.utilities.path_splitter import split_path_with_bsa
from core.utilities.xml_utils import beautify_xml, split_frames, unsplit_frames


class Patcher:
    """
    Class for Patcher.
    """

    log: logging.Logger = logging.getLogger("Patcher")

    config: Config
    app_path: Path = get_current_path()
    cwd_path: Path = Path.cwd()

    ffdec_interface: FFDecInterface
    xdelta_interface: XDeltaInterface
    tmp_path: Optional[Path] = None

    def __init__(self, config: Config) -> None:
        self.config = config

        self.ffdec_interface = FFDecInterface()
        self.xdelta_interface = XDeltaInterface()

    def load_patch(self, path: Path) -> Patch:
        """
        Loads the patch from the specified path.

        Args:
            path (Path): The path to the patch file.

        Returns:
            Patch: The loaded patch.
        """

        return Patch.load(path)

    def patch_shapes(self, patch: Patch, temp_folder: Path) -> None:
        """
        Patches the shapes of the specified patch to the files at the specified path.

        Args:
            patch (Patch): The patch to run.
            temp_folder (Path): The path to the temp folder with the original files.
        """

        for patch_file in patch.files:
            if not patch_file.shapes:
                continue

            swf_file: Path = temp_folder / patch_file.original_file_path
            shapes: dict[Path, list[int]] = {
                patch.shapes_folder_path / shape_path: ids
                for shape_path, ids in patch_file.shapes.items()
            }
            self.ffdec_interface.replace_shapes(swf_file, shapes)

    def prepare_files(
        self, patch: Patch, original_mod_path: Path, temp_folder: Path
    ) -> None:
        """
        Copies all required files to patch to the temp folder.

        Args:
            patch (Patch): The patch to run.
            original_mod_path (Path): The path to the original mod.
            temp_folder (Path): The path to the temp folder.
        """

        self.log.info("Preparing mod files...")

        file: PatchFile
        bsa_file: Optional[Path]
        mod_file: Optional[Path]
        for file in patch.files:
            bsa_file, mod_file = split_path_with_bsa(file.original_file_path)

            if mod_file is None:
                self.log.error(
                    f"An error occured while splitting '{file.original_file_path}'."
                )
                self.log.debug(f"BSA file: {bsa_file}")
                self.log.debug(f"Mod file: {mod_file}")
                continue

            if bsa_file is not None:
                bsa_file = original_mod_path / bsa_file.name
            else:
                mod_file = mod_file.relative_to(patch.path)

            required: bool = not file.optional
            origin_path: Path = original_mod_path / mod_file
            dest_path: Path = temp_folder / mod_file

            if bsa_file is None:
                if is_file(origin_path):
                    mkdir(dest_path.parent)
                    shutil.copyfile(origin_path, dest_path)

                elif required:
                    raise FileNotFoundError(
                        f"'{origin_path}' is required but does not exist!"
                    )

                # Skip missing but optional SWF files
                else:
                    self.log.warning(
                        f"'{origin_path}' does not exist! Skipped patch file."
                    )

            elif is_file(bsa_file):
                bsa_archive = BSAArchive(bsa_file)
                bsa_archive.extract_file(mod_file, temp_folder / bsa_file.name)

            elif required:
                raise FileNotFoundError(f"'{bsa_file}' is required but does not exist!")

            # Skip missing but optional BSA files
            else:
                self.log.warning(f"'{bsa_file}' does not exist! Skipped patch file.")

        self.log.info("Mod files ready to patch.")

    def convert_swfs2xmls(self, patch: Patch, temp_folder: Path) -> None:
        """
        Converts the SWF files within the specified temp folder to XML files if they have
        a JSON patch file in the specified patch.

        Args:
            patch (Patch): Patch to run.
            temp_folder (Path): Temp folder with SWF files.
        """

        for patch_file in patch.files:
            swf_file: Path = temp_folder / patch_file.original_file_path

            if patch_file.type == PatchType.Json and patch_file.data:
                if is_file(swf_file):
                    self.ffdec_interface.swf2xml(swf_file)
                else:
                    self.log.error(
                        f"Failed to convert '{swf_file}' to XML file: File does not "
                        "exist."
                    )

    def convert_xmls2swfs(self, patch: Patch, temp_folder: Path) -> None:
        """
        Converts the XML files within the specified temp folder back to SWF files if they
        have a JSON patch file in the specified patch.

        Args:
            patch (Patch): Patch to run.
            temp_folder (Path): Temp folder with XML files.
        """

        for patch_file in patch.files:
            xml_file: Path = temp_folder / patch_file.original_file_path.with_suffix(
                ".xml"
            )

            if patch_file.type == PatchType.Json and patch_file.data:
                if is_file(xml_file):
                    self.ffdec_interface.xml2swf(xml_file)
                else:
                    self.log.error(
                        f"Failed to convert '{xml_file}' back to SWF file: File does "
                        "not exist."
                    )

    def patch_xmls(self, patch: Patch, temp_folder: Path) -> None:
        """
        Patches the XML files in the temp folder according to the patch's JSON files.

        Args:
            patch (Patch): Patch to run.
            temp_folder (Path): Temp folder with XML files.
        """

        for patch_file in patch.files:
            xml_file: Path = temp_folder / patch_file.original_file_path.with_suffix(
                ".xml"
            )

            if patch_file.type == PatchType.Json and patch_file.data:
                if is_file(xml_file):
                    self.patch_xml_file(xml_file, patch_file.data)
                else:
                    self.log.error(
                        f"Failed to patch '{xml_file}': File does not exist."
                    )

    def patch_xml_file(self, xml_file: Path, patch_data: list[PatchItem]) -> None:
        """
        Patches the specified XML file with the specified patch data.

        Args:
            xml_file (Path): XML file to patch.
            patch_data (list[PatchItem]): Patch data to apply.
        """

        self.log.info(
            f"Patching '{xml_file.name}' with {len(patch_data)} patch item(s)..."
        )

        xml_data: ET.ElementTree[ET.Element[str]] = ET.parse(str(xml_file))
        xml_root: ET.Element[str] = xml_data.getroot()

        if self.config.debug_mode:
            output_folder: Path = self.config.output_folder or self.cwd_path.parent
            mkdir(output_folder)
            _debug_json = (output_folder / f"{xml_file.stem}.json").resolve()
            # TODO: Reimplement
            # with open(_debug_json, "w", encoding="utf8") as file:
            #     file.write(json.dumps(data, indent=4))

        # split frames as they aren't indexed or whatsoever in the XML
        xml_root = split_frames(xml_root)

        for item in patch_data:
            filter: str = item.filter
            changes: dict[str, str] = item.changes
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

        # unsplit frames again
        xml_root = unsplit_frames(xml_root)

        self.log.info("Writing XML file...")
        with open(xml_file, "wb") as file:
            xml_data.write(file, encoding="utf8")

        # Optional debug XML file
        if self.config.debug_mode:
            output_folder: Path = self.config.output_folder or self.cwd_path.parent
            mkdir(output_folder)
            _debug_xml = (output_folder / f"{xml_file.name}").resolve()
            with open(_debug_xml, "w", encoding="utf8") as file:
                file.write(
                    beautify_xml(ET.tostring(xml_data.getroot(), encoding="unicode"))
                )
            self.log.debug(f"Debug written to '{_debug_xml}'.")

    def finalize_files(
        self,
        patch: Patch,
        temp_folder: Path,
        original_mod_path: Path,
        output_folder: Path,
        repack_bsas: bool,
    ) -> None:
        """
        Copies patched files to the output folder and repacks BSAs with patched files if
        enabled.

        Args:
            patch (Patch): Patch to run.
            temp_folder (Path): Temp folder with patched files.
            original_mod_path (Path): Path to original mod (for original BSAs).
            output_folder (Path): Output folder for repacked BSAs.
            repack_bsas (bool): Whether to repack BSAs.
        """

        bsa_archives: dict[Path, list[Path]] = {}
        """
        Stores path to BSAs with list of patched files.
        """

        mkdir(output_folder)

        bsa_file: Optional[Path]
        mod_file: Optional[Path]
        for file in patch.files:
            bsa_file, mod_file = split_path_with_bsa(file.original_file_path)

            if mod_file is None:
                self.log.error(
                    f"An error occured while splitting '{file.original_file_path}'."
                )
                self.log.debug(f"BSA file: {bsa_file}")
                self.log.debug(f"Mod file: {mod_file}")
                continue

            patched_file: Path = temp_folder / file.original_file_path

            # Skip missing SWF files
            if not is_file(patched_file):
                self.log.warning(f"Skipped missing patched file '{patched_file}'.")
                continue

            if bsa_file is not None and repack_bsas:
                bsa_file = original_mod_path / bsa_file
                bsa_archives.setdefault(bsa_file, []).append(mod_file)

            else:
                src: Path = patched_file
                dst: Path = output_folder / mod_file

                # Backup original file
                if is_file(dst):
                    os.rename(
                        dst,
                        dst.with_suffix(
                            dst.suffix + time.strftime(".%d-%m-%Y-%H-%M-%S")
                        ),
                    )

                mkdir(dst.parent)
                shutil.copyfile(src, dst)

        for bsa_file, files in bsa_archives.items():
            self.log.info(f"Repacking {bsa_file.name!r} with patched files...")

            # 1. Extract BSA to a new temp folder
            bsa_archive = BSAArchive(bsa_file)
            bsa_content_path: Path = temp_folder / ("out_" + bsa_file.name)
            mkdir(bsa_content_path)
            bsa_archive.extract(bsa_content_path)

            # 2. Copy patched files over original files
            for file in files:
                src: Path = temp_folder / bsa_file.name / file
                dst: Path = bsa_content_path / file

                # Remove original file from BSA
                if is_file(dst):
                    os.remove(dst)

                shutil.copyfile(src, dst)

            # 3. Repack BSA at output folder
            dst: Path = output_folder / bsa_file.name

            # Backup original BSA
            if is_file(dst):
                os.rename(
                    dst,
                    dst.with_suffix(dst.suffix + time.strftime(".%d-%m-%Y-%H-%M-%S")),
                )

            BSAArchive.create_archive(bsa_content_path, output_folder / bsa_file.name)

    def finish_patching(
        self, patch: Patch, temp_folder: Path, original_mod_path: Path
    ) -> None:
        output_folder: Path
        if self.config.output_folder is not None:
            output_folder = self.config.output_folder
        else:
            output_folder = self.cwd_path.parent

        self.finalize_files(
            patch,
            temp_folder,
            original_mod_path,
            output_folder,
            self.config.repack_bsas,
        )

        self.log.info(f"Output written to '{output_folder}'.")

    def get_tmp_dir(self) -> Path:
        """
        Returns the temporary directory used by the patcher. Creates one if it doesn't
        exist.

        Returns:
            Path: The temporary directory
        """

        if self.tmp_path is None:
            self.tmp_path = Path(tempfile.mkdtemp(prefix="DIP_"))
            self.log.debug(f"Created temporary directory at {str(self.tmp_path)!r}.")

        return self.tmp_path

    def apply_binary_patches(self, patch: Patch, temp_folder: Path) -> None:
        """
        Applies binary patches to the original files in the specified temp folder.

        Args:
            patch (Patch): The patch to run.
            temp_folder (Path): The temp folder containing copies of the original files.
        """

        binary_patches: list[PatchFile] = [
            file for file in patch.files if file.type == PatchType.Binary
        ]

        if not binary_patches:
            return

        self.log.info(f"Applying {len(binary_patches)} binary patch(es)...")

        for patch_file in binary_patches:
            swf_file: Path = temp_folder / patch_file.original_file_path
            bin_file: Path = patch.patch_folder_path / patch_file.path
            self.xdelta_interface.patch_file(swf_file, bin_file)

        self.log.info("Binary patches applied.")

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

        self.log.info("Patching mod...")

        start_time: float = time.time()
        temp_folder: Path = self.get_tmp_dir()

        # 0. Load patch data
        patch: Patch = Patch.load(patch_path)

        # 1. Setup JRE if required
        if any(file for file in patch.files if file.type == PatchType.Json):
            self.ffdec_interface.setup_jre(temp_folder)

        # 2. Copy original mod files to patch and extract BSAs if required
        self.prepare_files(patch, original_mod_path, temp_folder)

        # 3. Patch shapes
        self.patch_shapes(patch, temp_folder)

        # 4. Convert SWFs to XMLs
        self.convert_swfs2xmls(patch, temp_folder)

        # 5. Patch XMLs
        self.patch_xmls(patch, temp_folder)

        # 6. Convert XMLs back to SWFs
        self.convert_xmls2swfs(patch, temp_folder)

        # 7. Apply binary patches with xdelta
        self.apply_binary_patches(patch, temp_folder)

        # 8. Copy patched files back to current directory and repack BSAs if enabled
        self.finish_patching(patch, temp_folder, original_mod_path)

        duration: float = time.time() - start_time
        self.log.info(f"Patching complete in {duration:.3f} second(s).")

        return duration

    def clean(self) -> None:
        if self.tmp_path is not None and is_dir(self.tmp_path):
            shutil.rmtree(self.tmp_path, ignore_errors=True)
            self.tmp_path = None
            self.log.info("Removed temporary folder.")
