"""
Copyright (c) Cutleast
"""

from __future__ import annotations

from dataclasses import field
from pathlib import Path
from typing import Any, Optional

import jstyleson as json
from pydantic import BaseModel

from core.utilities.xml_utils import parse_xpath_part

from .patch_item import PatchItem
from .patch_type import PatchType


class PatchFile(BaseModel):
    """
    Model representing a single patch file and its data.
    """

    path: Path
    """The path to the file, relative to its patch's "Patch" folder."""

    type: PatchType
    """The type of the patch file. Determines how the file is handled."""

    optional: bool
    """Whether the patch file is optional for the entire patch to succeed."""

    data: list[PatchItem] = field(default_factory=list)
    """The data of the patch file. Empty if it's a binary patch."""

    shapes: dict[Path, list[int]] = field(default_factory=dict)
    """
    The shapes and their ids to replace for this patch. Empty if it's a binary patch.
    The shapes' paths are **relative to the patch's shapes folder - not this file**.
    """

    @property
    def original_file_path(self) -> Path:
        """
        Returns the file path of the original file that is patched by this file.

        Returns:
            Path: File path, relative to the patch/original mod
        """

        return self.path.with_suffix(".swf")

    @staticmethod
    def load(path: Path, patch_path: Path) -> PatchFile:
        """
        Loads a patch file and returns a PatchFile object with the adequate type,
        determined by the file extension.

        Args:
            path (Path): Path to file
            patch_path (Path): Path to the patch, for making the file path relative

        Raises:
            NotImplementedError: If the file type is not supported

        Returns:
            PatchFile: PatchFile object
        """

        match path.suffix.lower():
            case ".json":
                json_data: dict = json.loads(path.read_text(encoding="utf-8"))

                return PatchFile(
                    path=path.relative_to(patch_path),
                    type=PatchType.Json,
                    optional=json_data.get("optional", False),
                    data=PatchFile.__process_patch_data(json_data.get("swf", {})),
                    shapes=PatchFile.__process_shapes(json_data.get("shapes", [])),
                )

            case ".bin":
                return PatchFile(
                    path=path.relative_to(patch_path),
                    type=PatchType.Binary,
                    optional=False,
                )

            case _:
                raise NotImplementedError(f"Unsupported patch file type: {path.suffix}")

    @staticmethod
    def __process_shapes(shapes_data: list[dict[str, str]]) -> dict[Path, list[int]]:
        """
        Processes shapes data and returns a dictionary mapping shape paths and lists of
        ids.

        Example:
        ```
        [
            {
                "id": "1,2,5,7,9",
                "fileName": "example.svg"
            }
        ]
        ==>
        {
            Path("example.svg"): [1, 2, 5, 7, 9]
        }
        ```

        Args:
            shapes_data (list[dict[str, str]]): Raw JSON data to process.

        Returns:
            dict[Path, list[int]]: Processed shapes data.
        """

        shapes: dict[Path, list[int]] = {}
        for shape_item in shapes_data:
            shape_path = Path(shape_item["fileName"])
            if shape_item["id"].strip():
                shapes.setdefault(shape_path, []).extend(
                    [int(shape_id) for shape_id in shape_item["id"].split(",")]
                )

        return shapes

    @staticmethod
    def __process_patch_data(patch_data: dict) -> list[PatchItem]:
        """
        Processes patch data and returns a list of patch items.

        Args:
            patch_data (dict): Raw JSON data to process.

        Returns:
            list[PatchItem]: Processed patch items.
        """

        result: list[PatchItem] = []

        def process_data_helper(
            data: dict[str, Any] | list, cur_filter: str = ""
        ) -> Optional[PatchItem]:
            cur_result: Optional[PatchItem] = None
            cur_changes: dict[str, str] = {}

            if isinstance(data, list):
                for item in data:
                    if child_result := process_data_helper(item, cur_filter + "/item"):
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
                            cur_result = PatchItem(
                                filter=cur_filter, changes=cur_changes
                            )
                    else:
                        if child_result := process_data_helper(
                            value, cur_filter + f"/{key}"
                        ):
                            result.append(child_result)

            return cur_result

        if cur_result := process_data_helper(patch_data):
            result.append(cur_result)

        return result

    def dump(self, list_tags: list[str]) -> dict[str, Any]:
        """
        Dumps the shapes and patch data of this file to a dictionary, fit for JSON
        serialization.

        Args:
            list_tags (list[str]):
                Tags that contain multiple children of same type. These tags are grouped
                in a list instead of overwriting each other in the same dict section.

        Returns:
            dict[str, Any]: Dumped shapes and patch data.
        """

        return {
            "shapes": self.__dump_shapes(),
            "swf": self.__dump_patch_items(list_tags),
        }

    def __dump_shapes(self) -> list[dict[str, str]]:
        """
        Dumps its shapes to a list of dictionaries, fit for JSON serialization.

        Returns:
            list[dict[str, str]]: Dumped shapes.
        """

        result: list[dict[str, str]] = []
        for shape_path, shape_ids in self.shapes.items():
            result.append(
                {"id": ",".join(map(str, shape_ids)), "fileName": str(shape_path)}
            )

        result.sort(key=lambda s: int(s["id"].split(",")[0]))  # sort after the first id

        return result

    def __dump_patch_items(self, list_tags: list[str]) -> dict[str, Any]:
        """
        Dumps its patch items to a single dictionary, fit for JSON serialization.

        Args:
            list_tags (list[str]):
                Tags that contain multiple children of same type. These tags are grouped
                in a list instead of overwriting each other in the same dict section.

        Returns:
            dict[str, Any]: Dumped patch items.
        """

        result: dict[str, Any] = {}

        for patch_item in self.data:
            xpath: str = patch_item.filter
            xpath_parts: list[str] = xpath.split("/")

            cur_section: dict[str, Any] | list[dict[str, Any]] = result
            for part in xpath_parts:
                if not part.strip() or part.strip() == ".":
                    continue

                tag: str
                attr_filters: dict[str, str]
                tag, attr_filters = parse_xpath_part(part)

                filter_dict: dict[str, str] = {
                    f"#{key}": value for key, value in attr_filters.items()
                }

                if isinstance(cur_section, dict):
                    cur_section = cur_section.setdefault(
                        tag, [] if tag in list_tags else {}
                    )
                else:
                    matching_item: Optional[dict[str, Any]] = (
                        PatchFile.__get_item_with_filter(filter_dict, cur_section)
                    )
                    if not matching_item:
                        cur_section.append({})
                        cur_section = cur_section[-1]
                    else:
                        cur_section = matching_item

                if filter_dict:
                    if isinstance(cur_section, dict):
                        cur_section.update(filter_dict)
                    else:
                        cur_section.append(filter_dict)

            if isinstance(cur_section, list):
                cur_section = cur_section[-1]  # type: ignore

            cur_section.update(
                {f"~{key}": value for key, value in patch_item.changes.items()}
            )

        return result

    @staticmethod
    def __get_item_with_filter(
        filter: dict[str, str], items: list[dict[str, Any]]
    ) -> Optional[dict[str, Any]]:
        """
        Checks if one of the specified items matches the specified filter.

        Args:
            filter (dict[str, str]): Filter to check.
            items (list[dict[str, Any]]): Items to check.

        Returns:
            Optional[dict[str, Any]]:
                The item that matches the filter, or None if no match is found.
        """

        for item in items:
            item_filter: dict[str, str] = {
                key: value for key, value in item.items() if key.startswith("#")
            }

            if item_filter == filter:
                return item
