"""
Copyright (c) Cutleast
"""

from pathlib import Path

import pytest

from core.patch.patch_file import PatchFile
from core.patch.patch_item import PatchItem
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
