"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Any

import pytest

from core.patch.patch_file import PatchFile
from core.patch.patch_item import PatchItem
from core.patch.patch_type import PatchType
from tests.base_test import BaseTest
from tests.utils import Utils


class TestPatchFile(BaseTest):
    """
    Tests `core.patch.patch_file.PatchFile`.
    """

    @staticmethod
    def process_shapes_stub(shapes_data: list[dict[str, str]]) -> dict[Path, list[int]]:
        """Stub for accessing the private PatchFile.__process_shapes()-method."""

        raise NotImplementedError

    @staticmethod
    def process_patch_data_stub(patch_data: dict) -> list[PatchItem]:
        """Stub for accessing the private PatchFile.__process_patch_data()-method."""

        raise NotImplementedError

    @staticmethod
    def dump_shapes_stub() -> list[dict[str, str]]:
        """Stub for accessing the private PatchFile.__dump_shapes()-method."""

        raise NotImplementedError

    @staticmethod
    def dump_patch_items_stub(list_tags: list[str]) -> dict[str, Any]:
        """Stub for accessing the private PatchFile.__dump_patch_items()-method."""

        raise NotImplementedError

    PROCESS_SHAPES_DATA: list[tuple[list[dict[str, str]], dict[Path, list[int]]]] = [
        (
            [{"id": "1,2,5,7,9", "fileName": "example.svg"}],
            {Path("example.svg"): [1, 2, 5, 7, 9]},
        ),
        ([{"id": "1", "fileName": "example2.svg"}], {Path("example2.svg"): [1]}),
        ([{"id": "", "fileName": "example3.svg"}], {}),
    ]

    @pytest.mark.parametrize("shapes_data, expected_shapes", PROCESS_SHAPES_DATA)
    def test_process_shapes(
        self, shapes_data: list[dict[str, str]], expected_shapes: dict[Path, list[int]]
    ) -> None:
        """
        Tests the processing of the replacement shapes data of a patch file.

        Args:
            shapes_data (list[dict[str, str]]): Raw JSON data to process.
            expected_shapes (dict[Path, list[int]]): Expected processed shapes data.
        """

        # given
        process_shapes = Utils.get_private_static_method(
            PatchFile, "process_shapes", TestPatchFile.process_shapes_stub
        )

        # when
        actual_shapes: dict[Path, list[int]] = process_shapes(shapes_data)

        # then
        assert actual_shapes == expected_shapes

    PROCESS_PATCH_DATA: list[tuple[dict, list[PatchItem]]] = [
        (
            {
                "displayRect": {
                    "~Xmax": "25600",
                    "~Xmin": "0",
                    "~Ymax": "14400",
                    "~Ymin": "0",
                },
                "tags": [
                    {
                        "#type": "DefineSpriteTag",
                        "#spriteId": "3",
                        "subTags": [
                            {
                                "#type": "PlaceObject2Tag",
                                "#characterId": "2",
                                "#depth": "1",
                                "~placeFlagHasMatrix": "true",
                            },
                            {
                                "#type": "PlaceObject2Tag",
                                "#characterId": "2",
                                "#depth": "1",
                                "matrix": {
                                    "~hasScale": "true",
                                    "~scaleX": "0",
                                    "~scaleY": "0",
                                },
                            },
                        ],
                    },
                    {
                        "#type": "DefineEditTextTag",
                        "#characterID": "5",
                        "textColor": {
                            "~type": "RGBA",
                            "~alpha": "255",
                            "~blue": "255",
                            "~green": "255",
                            "~red": "255",
                        },
                    },
                ],
            },
            [
                PatchItem(
                    filter="/displayRect",
                    changes={
                        "Xmax": "25600",
                        "Xmin": "0",
                        "Ymax": "14400",
                        "Ymin": "0",
                    },
                ),
                PatchItem(
                    filter="/tags/item[@type='DefineSpriteTag'][@spriteId='3']/subTags/item[@type='PlaceObject2Tag'][@characterId='2'][@depth='1']",
                    changes={"placeFlagHasMatrix": "true"},
                ),
                PatchItem(
                    filter="/tags/item[@type='DefineSpriteTag'][@spriteId='3']/subTags/item[@type='PlaceObject2Tag'][@characterId='2'][@depth='1']/matrix",
                    changes={"hasScale": "true", "scaleX": "0", "scaleY": "0"},
                ),
                PatchItem(
                    filter="/tags/item[@type='DefineEditTextTag'][@characterID='5']/textColor",
                    changes={
                        "alpha": "255",
                        "blue": "255",
                        "green": "255",
                        "red": "255",
                        "type": "RGBA",
                    },
                ),
            ],
        )
    ]

    @pytest.mark.parametrize("patch_data, expected_patch_items", PROCESS_PATCH_DATA)
    def test_process_patch_data(
        self, patch_data: dict, expected_patch_items: list[PatchItem]
    ) -> None:
        """
        Tests the processing of the patch data of a patch file.

        Args:
            patch_data (dict): Raw JSON data to process.
            expected_patch_items (list[PatchItem]): Expected processed patch items.
        """

        # given
        process_patch_data = Utils.get_private_static_method(
            PatchFile, "process_patch_data", TestPatchFile.process_patch_data_stub
        )

        # when
        actual_patch_items: list[PatchItem] = process_patch_data(patch_data)

        # then
        assert actual_patch_items == expected_patch_items

    DUMP_SHAPES_DATA: list[tuple[dict[Path, list[int]], list[dict[str, str]]]] = [
        (
            {
                Path("test1.svg"): [1, 2, 3],
                Path("test2.png"): [4, 5, 6],
                Path("test3.jpg"): [7, 8, 9],
            },
            [
                {"id": "1,2,3", "fileName": "test1.svg"},
                {"id": "4,5,6", "fileName": "test2.png"},
                {"id": "7,8,9", "fileName": "test3.jpg"},
            ],
        )
    ]

    @pytest.mark.parametrize("shapes, expected_shapes", DUMP_SHAPES_DATA)
    def test_dump_shapes(
        self, shapes: dict[Path, list[int]], expected_shapes: list[dict[str, str]]
    ) -> None:
        """
        Tests the dumping of the shapes of a patch file.

        Args:
            shapes (dict[Path, list[int]]): Shapes to dump.
            expected_shapes (list[dict[str, str]]): Expected dumped shapes data.
        """

        # given
        patch_file = PatchFile(
            path=Path(), type=PatchType.Json, optional=False, shapes=shapes
        )

        # when
        actual_shapes: list[dict[str, str]] = Utils.get_private_method(
            patch_file, "dump_shapes", TestPatchFile.dump_shapes_stub
        )()

        # then
        assert actual_shapes == expected_shapes

    DUMP_PATCH_DATA: list[tuple[list[PatchItem], dict[str, Any]]] = [
        (
            [
                PatchItem(
                    filter="./displayRect",
                    changes={
                        "Xmax": "25600",
                        "Xmin": "0",
                        "Ymax": "14400",
                        "Ymin": "0",
                    },
                ),
                PatchItem(
                    filter="./tags/item[@type='DefineSpriteTag'][@spriteId='3']/subTags/item[@type='PlaceObject2Tag'][@characterId='2'][@depth='1']",
                    changes={"placeFlagHasMatrix": "true"},
                ),
                PatchItem(
                    filter="./tags/item[@type='DefineSpriteTag'][@spriteId='3']/subTags/item[@type='PlaceObject2Tag'][@characterId='2'][@depth='1']/matrix",
                    changes={"hasScale": "true", "scaleX": "0", "scaleY": "0"},
                ),
                PatchItem(
                    filter="/tags/item[@type='DefineEditTextTag'][@characterID='5']/textColor",
                    changes={
                        "alpha": "255",
                        "blue": "255",
                        "green": "255",
                        "red": "255",
                        "type": "RGBA",
                    },
                ),
            ],
            {
                "displayRect": {
                    "~Xmax": "25600",
                    "~Xmin": "0",
                    "~Ymax": "14400",
                    "~Ymin": "0",
                },
                "tags": [
                    {
                        "#type": "DefineSpriteTag",
                        "#spriteId": "3",
                        "subTags": [
                            {
                                "#type": "PlaceObject2Tag",
                                "#characterId": "2",
                                "#depth": "1",
                                "~placeFlagHasMatrix": "true",
                                "matrix": {
                                    "~hasScale": "true",
                                    "~scaleX": "0",
                                    "~scaleY": "0",
                                },
                            },
                        ],
                    },
                    {
                        "#type": "DefineEditTextTag",
                        "#characterID": "5",
                        "textColor": {
                            "~type": "RGBA",
                            "~alpha": "255",
                            "~blue": "255",
                            "~green": "255",
                            "~red": "255",
                        },
                    },
                ],
            },
        )
    ]

    @pytest.mark.parametrize("patch_items, expected_patch_data", DUMP_PATCH_DATA)
    def test_dump_patch_data(
        self, patch_items: list[PatchItem], expected_patch_data: dict[str, Any]
    ) -> None:
        """
        Tests the dumping of the patch data of a patch file.

        Args:
            patch_items (list[PatchItem]): Patch items to dump.
            expected_patch_data (dict[str, Any]): Expected dumped patch data.
        """

        # given
        patch_file = PatchFile(
            path=Path(), type=PatchType.Json, optional=False, data=patch_items
        )

        # when
        actual_patch_data: dict[str, Any] = Utils.get_private_method(
            patch_file, "dump_patch_items", TestPatchFile.dump_patch_items_stub
        )(["tags", "subTags"])

        # then
        assert actual_patch_data == expected_patch_data
