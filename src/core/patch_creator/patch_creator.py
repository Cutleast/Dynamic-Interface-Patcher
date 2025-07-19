"""
Copyright (c) Cutleast
"""

import json
import logging
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
from core.config.patch_creator_config import PatchCreatorConfig
from core.patch.patch import Patch
from core.patch.patch_file import PatchFile
from core.patch.patch_item import PatchItem
from core.patch.patch_type import PatchType
from core.patcher.patcher import Patcher
from core.utilities.filesystem import is_dir, is_file, mkdir
from core.utilities.glob import glob
from core.utilities.xml_utils import split_frames


class PatchCreator:
    """
    Class for patch creator.
    """

    log: logging.Logger = logging.getLogger("PatchCreator")

    config: Config
    patch_creator_config: PatchCreatorConfig
    cwd_path: Path = Path.cwd()

    ffdec_interface: FFDecInterface
    xdelta_interface: XDeltaInterface
    tmp_path: Optional[Path] = None

    def __init__(
        self, config: Config, patch_creator_config: PatchCreatorConfig
    ) -> None:
        self.config = config
        self.patch_creator_config = patch_creator_config

        self.ffdec_interface = FFDecInterface()
        self.xdelta_interface = XDeltaInterface()

    def load_raw_patch(self, patched_mod_path: Path) -> Patch:
        """
        Loads a raw (with actual SWF files instead of JSONs and BINs) patch.

        Args:
            patched_mod_path (Path): The path to the patched mod.

        Returns:
            Patch: The loaded patch
        """

        self.log.info(f"Loading patched mod from '{patched_mod_path}'...")

        patch_files: list[PatchFile] = []
        for swf_file in patched_mod_path.glob("**/*.swf"):
            if swf_file.name in self.patch_creator_config.file_blacklist:
                continue

            patch_files.append(
                PatchFile(
                    path=swf_file.relative_to(patched_mod_path).with_suffix(".json"),
                    type=PatchType.Json,
                    optional=False,
                )
            )

        patch = Patch(
            path=self.config.output_folder or self.cwd_path, files=patch_files
        )
        self.log.info(f"Loaded patched mod with {len(patch.files)} SWF file(s).")

        return patch

    def prepare_files(
        self,
        patch: Patch,
        patched_mod_path: Path,
        original_mod_path: Path,
        temp_folder: Path,
    ) -> None:
        """
        Copies all required files (and extracts any BSAs with SWF files) to the temp
        folder.

        Args:
            patch (Patch): Blank patch.
            patched_mod_path (Path): Path to patched mod.
            original_mod_path (Path): Path to original mod.
            temp_folder (Path): Path to temp folder.
        """

        self.log.info("Preparing files for patch creation...")

        self.__prepare_patched_files(patch, patched_mod_path, temp_folder)
        self.__prepare_original_files(patch, original_mod_path, temp_folder)

        self.log.info("Patched and original files are ready for patch creation.")

    def __prepare_patched_files(
        self, patch: Patch, patched_mod_path: Path, temp_folder: Path
    ) -> None:
        """
        Prepares the patched files for the patch by copying them to the specified temp folder.

        Args:
            patch (Patch): Blank patch.
            patched_mod_path (Path): Path to patched mod.
            temp_folder (Path): Path to temp folder.
        """

        for file in patch.files:
            src_path: Path = patched_mod_path / file.original_file_path
            dst_path: Path = temp_folder / "Patch" / file.original_file_path

            mkdir(dst_path.parent)
            shutil.copyfile(src_path, dst_path)
            self.log.debug(f"Copied '{src_path}' -> '{dst_path}'.")

    def __prepare_original_files(
        self, patch: Patch, original_mod_path: Path, temp_folder: Path
    ) -> None:
        """
        Prepares the original files for the patch by copying them to the specified temp
        folder. Extracts the files from BSAs if necessary.

        Args:
            patch (Patch): Blank patch.
            original_mod_path (Path): Path to original mod.
            temp_folder (Path): Path to temp folder.
        """

        for file in patch.files:
            src_path: Path = original_mod_path / file.original_file_path
            dst_path: Path = temp_folder / "Original" / file.original_file_path

            mkdir(dst_path.parent)
            if is_file(src_path):
                shutil.copyfile(src_path, dst_path)
                self.log.debug(f"Copied '{src_path}' -> '{dst_path}'.")
            else:
                for bsa_file in original_mod_path.glob("*.bsa"):
                    bsa_archive = BSAArchive(bsa_file)
                    if file.original_file_path in list(map(Path, bsa_archive.files)):
                        break

                else:
                    raise FileNotFoundError(
                        f"File '{file.original_file_path}' not found in original mod."
                    )

                bsa_archive.extract_file(
                    filename=file.original_file_path,
                    dest_folder=temp_folder / "Original",
                )
                self.log.debug(
                    f"Extracted '{file.original_file_path}' -> "
                    f"'{temp_folder / 'Original' / file.original_file_path}'."
                )

    def convert_patched_files_to_xmls(self, patch: Patch, temp_folder: Path) -> None:
        """
        Converts the patched files at the temp folder for the patch to XML files for
        later comparison.

        Args:
            patch (Patch): Blank patch.
            temp_folder (Path): Path to temp folder with patched files.
        """

        self.log.info("Converting patched files to XML files...")

        for file in patch.files:
            swf_file: Path = temp_folder / "Patch" / file.original_file_path
            self.ffdec_interface.swf2xml(swf_file)

    def convert_original_files_to_xmls(self, patch: Patch, temp_folder: Path) -> None:
        """
        Converts the original files at the temp folder for the patch to XML files for
        later comparison.

        Args:
            patch (Patch): Blank patch.
            temp_folder (Path): Path to temp folder with original files.
        """

        self.log.info("Converting original files to XML files...")

        for file in patch.files:
            swf_file: Path = temp_folder / "Original" / file.original_file_path
            self.ffdec_interface.swf2xml(swf_file)

    def extract_different_shapes(self, patch: Patch, temp_folder: Path) -> None:
        """
        Extracts different shapes to `temp_folder`/Output/Shapes and adds shapes to the
        patch's data.

        Args:
            patch (Patch): Patch to create.
            temp_folder (Path): Path to temp folder with patched and original files.
        """

        self.log.info("Extracting different shapes...")
        shapes_folder: Path = temp_folder / "Output" / "Shapes"

        for file in patch.files:
            patched_xml_file: Path = (
                temp_folder / "Patch" / file.original_file_path.with_suffix(".xml")
            )
            patched_swf_file: Path = patched_xml_file.with_suffix(".swf")
            original_xml_file: Path = (
                temp_folder / "Original" / file.original_file_path.with_suffix(".xml")
            )

            original_xml: ET.ElementTree[ET.Element[str]] = ET.parse(
                str(original_xml_file)
            )
            patched_xml: ET.ElementTree[ET.Element[str]] = ET.parse(
                str(patched_xml_file)
            )

            different_shapes: list[int] = self.get_different_shapes(
                original_xml,  # type: ignore
                patched_xml,  # type: ignore
            )

            if not different_shapes:
                continue

            outpath: Path = shapes_folder / patched_swf_file.stem
            mkdir(outpath)

            self.ffdec_interface.export_shapes(
                swf_file=patched_swf_file,
                shape_ids=different_shapes,
                outpath=outpath,
                format=self.patch_creator_config.export_format,
            )

            for shape in glob(outpath, "*", recursive=False):
                shape_id: str = shape.stem
                file.shapes.setdefault(
                    patched_swf_file.stem / shape.relative_to(outpath), []
                ).append(int(shape_id))

    def get_different_shapes(
        self, original_xml: ET.ElementTree, patched_xml: ET.ElementTree
    ) -> list[int]:
        """
        Compares the specified xml doms and returns a list of different shape ids.

        Args:
            original_xml (ET.ElementTree): Original XML dom.
            patched_xml (ET.ElementTree): Patched XML dom.

        Returns:
            list[int]: List of different shape ids.
        """

        different_shapes: list[int] = []

        original_shapes: list[ET.Element] = []
        for shape_type in self.patch_creator_config.shape_types:
            original_shapes += original_xml.findall(
                f"*/item[@type='{shape_type}'][@shapeId]"
            )

        for original_shape in original_shapes:
            shape_id: str = original_shape.attrib["shapeId"]
            shape_type: str = original_shape.attrib["type"]

            patched_xpath = f"*/item[@type='{shape_type}'][@shapeId='{shape_id}']"
            patched_shape = patched_xml.find(patched_xpath)
            if PatchCreator.check_if_different(original_shape, patched_shape):
                different_shapes.append(int(shape_id))

        return different_shapes

    @staticmethod
    def check_if_different(
        elem1: Optional[ET.Element], elem2: Optional[ET.Element]
    ) -> bool:
        """
        Compares two XML elements and returns whether they are different.
        This function compares the elements recursively.

        Args:
            elem1 (Optional[ET.Element]): First XML element or None.
            elem2 (Optional[ET.Element]): Second XML element or None.

        Returns:
            bool: If the elements are different.
        """

        # Check if one of the elements is None
        if elem1 is None or elem2 is None:
            return elem1 == elem2

        # Check if element attributes are different
        if elem1.attrib != elem2.attrib:
            return True

        # Compare children recursively
        for child1, child2 in zip(elem1, elem2):
            if PatchCreator.check_if_different(child1, child2):
                return True

        return False

    def create_patch_data(self, patch: Patch, temp_folder: Path) -> None:
        """
        Creates patch data by comparing patched XML files with original XML files and
        storing the differences with filters in `PatchItem` objects.

        Args:
            patch (Patch): Patch to create.
            temp_folder (Path): Path to temp folder with patched and original XML files.
        """

        self.log.info("Creating patch data...")

        for file in patch.files:
            patched_xml_file: Path = (
                temp_folder / "Patch" / file.original_file_path.with_suffix(".xml")
            )
            original_xml_file: Path = (
                temp_folder / "Original" / file.original_file_path.with_suffix(".xml")
            )

            original_xml: ET.Element[str] = ET.parse(str(original_xml_file)).getroot()
            patched_xml: ET.Element[str] = ET.parse(str(patched_xml_file)).getroot()

            # prepare xmls by splitting the unindexed frame tags
            # similar to what the patcher does before applying the patch
            original_xml = split_frames(original_xml)
            patched_xml = split_frames(patched_xml)

            patch_items: list[PatchItem] = self.create_patch_items(
                original_xml, patched_xml, ".", "swf"
            )
            file.data = patch_items

            self.log.info(
                f"Created {len(patch_items)} patch item(s) from XML differences in "
                f"'{file.original_file_path}'."
            )

    def create_patch_items(
        self,
        original_root: ET.Element,
        patched_element: ET.Element,
        cur_xpath: str,
        root: str,
    ) -> list[PatchItem]:
        """
        Creates a list of `PatchItem` objects by comparing the specified XML elements
        and their children.

        Args:
            original_root (ET.Element): XML **root** element from original SWF file.
            patched_element (ET.Element): XML element from patched SWF file.
            cur_xpath (str): Current XPath (for recursive calls).
            root (str): Root tag of the XML element.

        Returns:
            list[PatchItem]: List of `PatchItem` objects.
        """

        type_blacklist: list[str] = self.patch_creator_config.type_blacklist
        tag_blacklist: list[str] = self.patch_creator_config.tag_blacklist
        filter_whitelist: list[str] = self.patch_creator_config.filter_whitelist
        attr_blacklist: list[str] = self.patch_creator_config.attr_blacklist
        creation_whitelist: list[str] = self.patch_creator_config.creation_whitelist

        result: dict[str, PatchItem] = {}

        element_type: str = patched_element.get("type", "item")
        element_tag: str = patched_element.tag

        if element_type not in type_blacklist and element_tag not in tag_blacklist:
            if element_tag != root:
                cur_xpath += "/" + element_tag

                # find original element because element order may differ
                for key, value in patched_element.items():
                    if key not in filter_whitelist:
                        continue

                    cur_xpath += f"[@{key}='{value}']"

            original_element: Optional[ET.Element[str]] = original_root.find(cur_xpath)

            if original_element is not None:
                # compare attributes of the current elements
                for attr, value in patched_element.items():
                    original_value: Optional[str] = original_element.get(attr)

                    if (
                        value != original_value
                        and attr not in attr_blacklist + filter_whitelist
                    ):
                        patch_item: PatchItem = result.setdefault(
                            cur_xpath, PatchItem(cur_xpath, {})
                        )
                        patch_item.changes[attr] = value

            elif element_tag in creation_whitelist:
                self.log.debug(f"Creating element '{element_tag}' at '{cur_xpath}'...")

                patch_item: PatchItem = result.setdefault(
                    cur_xpath, PatchItem(cur_xpath, {})
                )
                patch_item.changes.update(
                    {
                        attr: value
                        for attr, value in patched_element.items()
                        if attr not in attr_blacklist
                    }
                )

        # iterate child elements
        for child in patched_element.findall("./"):
            child_result: list[PatchItem] = self.create_patch_items(
                original_root, child, cur_xpath, root
            )
            # merge results
            for patch_item in child_result:
                if patch_item.filter in result:
                    result[patch_item.filter].changes.update(patch_item.changes)
                else:
                    result[patch_item.filter] = patch_item

        return list(result.values())

    def create_output(self, patch: Patch, temp_folder: Path) -> Path:
        """
        Creates the finished output folder at the specified temp folder with all
        required patch files and shapes.

        Args:
            patch (Patch): Patch to create.
            temp_folder (Path): Path to temp folder.

        Returns:
            Path: Path to output folder with all required files
        """

        output_folder: Path = temp_folder / "Output"
        mkdir(output_folder)

        self.log.info(f"Creating output at '{output_folder}'...")

        for file in patch.files:
            patch_folder: Path = output_folder / "Patch"
            mkdir(patch_folder)
            dest_file: Path = patch_folder / file.original_file_path.with_suffix(
                ".json"
            )
            mkdir(dest_file.parent)
            dest_file.write_text(
                json.dumps(
                    file.dump(self.patch_creator_config.list_tags),
                    indent=4,
                )
            )
            self.log.debug(f"Dumped '{file.original_file_path}' to '{dest_file}'.")

        return output_folder

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

    def create_patch(self, patched_mod_path: Path, original_mod_path: Path) -> float:
        """
        Creates patch data by comparing patched mod with original mod:

        0. Create temp folder and setup JRE
        1. Load patched mod and create a blank DIP patch at the output folder.
        2. Copy patched mod and original mod to a temp folder.
           Extract original mod files from BSAs if required and possible.
        3. Convert patched and original SWFs to XMLs.
        4. Compare patched and original XMLs and export different shapes via ffdec
           commandline.

        The following three steps are required since FFDec makes more changes
        to a file than just the shapes themselves when replacing shapes.
        Therefore, the shapes are replaced in the original files to avoid obsolete differences.

        5. Replace shapes of the original file.
        6. Convert original SWFs with replaced shapes to XMLs, again.
        7. Compare original and patched file.

        And then to finish the patch:

        8. Create output folder with JSON files for each modified SWF.
        9. Copy finished patch data to the configured output folder or
        `<current directory>/Output`.

        Args:
            patched_mod_path (Path): Path to the patched mod.
            original_mod_path (Path): Path to the original mod.

        Returns:
            float: Duration in seconds
        """

        self.log.info(
            f"Creating DIP patch from '{patched_mod_path}' with original mod at "
            f"'{original_mod_path}'..."
        )

        start_time: float = time.time()

        if self.config.debug_mode:
            self.patch_creator_config.print_settings_to_log()

        # 0. Create temp folder and setup JRE
        temp_folder: Path = self.get_tmp_dir()
        self.ffdec_interface.setup_jre(temp_folder)

        # 1. Load patched mod
        patch: Patch = self.load_raw_patch(patched_mod_path)

        # 2. Copy patched mod and original mod to temp folder
        self.prepare_files(patch, patched_mod_path, original_mod_path, temp_folder)

        # 3. Convert patched and original SWFs to XMLs
        self.convert_patched_files_to_xmls(patch, temp_folder)
        self.convert_original_files_to_xmls(patch, temp_folder)

        # 4. Export different shapes
        self.extract_different_shapes(patch, temp_folder)

        # 5. Replace shapes of the original files
        patch.path = temp_folder / "Output"
        Patcher.patch_shapes(patch, temp_folder / "Original", self.ffdec_interface)

        # 6. Reconvert original files with replaced shapes to XMLs
        self.convert_original_files_to_xmls(patch, temp_folder)

        # 7. Compare original and patched files
        self.create_patch_data(patch, temp_folder)

        # 8. Create output folder with JSON files for each modified SWF
        temp_output_folder: Path = self.create_output(patch, temp_folder)

        # 9. Copy finished patch data to the configured output folder or
        # `<current directory>/Output`
        final_output_folder: Path = (
            self.config.output_folder or self.cwd_path / "Output"
        )
        mkdir(final_output_folder)
        shutil.copytree(temp_output_folder, final_output_folder, dirs_exist_ok=True)
        self.log.debug(f"Copied '{temp_output_folder}' -> '{final_output_folder}'.")

        duration: float = time.time() - start_time
        self.log.info(f"Patch created in {duration:.3f} second(s).")

        return duration

    def clean(self) -> None:
        if self.tmp_path is not None and is_dir(self.tmp_path):
            shutil.rmtree(self.tmp_path, ignore_errors=True)
            self.tmp_path = None
            self.log.info("Removed temporary folder.")
