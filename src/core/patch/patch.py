"""
Copyright (c) Cutleast
"""

from __future__ import annotations

import logging
from pathlib import Path

from pydantic.dataclasses import dataclass

from core.patch.patch_type import PatchType
from core.utilities.cache import cache
from core.utilities.glob import glob

from .patch_file import PatchFile


@dataclass(kw_only=True)
class Patch:
    """
    Dataclass representing a patch.
    """

    path: Path
    """The path to the patch's root folder."""

    files: list[PatchFile]
    """The files in the patch."""

    @property
    def patch_folder_path(self) -> Path:
        """
        The path to the patch's Patch folder containing the actual patch files.
        """

        return self.path / "Patch"

    @property
    def shapes_folder_path(self) -> Path:
        """
        The path to the patch's Shapes folder containing the replacement shapes of the
        patch.
        """

        return self.path / "Shapes"

    @classmethod
    @cache
    def get_logger(cls) -> logging.Logger:
        return logging.getLogger("Patch")

    @staticmethod
    def load(path: Path) -> Patch:
        """
        Loads a patch and all its files from the specified path.

        Args:
            path (Path): The path to the patch's root folder.

        Returns:
            Patch: The loaded patch.
        """

        file_paths: list[Path] = [
            f for suffix in PatchType for f in glob(path / "Patch", "*" + suffix)
        ]

        files: list[PatchFile] = []
        for file_path in file_paths:
            try:
                files.append(PatchFile.load(file_path, path / "Patch"))
            except Exception as ex:
                Patch.get_logger().error(
                    f"Failed to load patch file '{file_path}': {ex}", exc_info=ex
                )

        Patch.get_logger().info(f"Loaded {len(files)} patch file(s) from '{path}'.")

        return Patch(path=path, files=files)
