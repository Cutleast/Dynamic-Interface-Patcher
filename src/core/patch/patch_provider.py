"""
Copyright (c) Cutleast
"""

import logging
from pathlib import Path

from core.utilities.filesystem import is_dir
from core.utilities.glob import glob


class PatchProvider:
    """
    Class for scanning and checking of potential patches.
    """

    log: logging.Logger = logging.getLogger("PatchProvider")

    cwd_path: Path = Path.cwd()

    @staticmethod
    def check_patch(folder: Path) -> bool:
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

    @staticmethod
    def get_patches() -> list[str]:
        """
        Returns a list of possible paths to patches.

        Returns:
            list[str]: List of possible paths to patches.
        """

        PatchProvider.log.debug("Scanning for patches...")

        paths_to_scan: list[Path] = [
            PatchProvider.cwd_path,
            PatchProvider.cwd_path.parent,
        ]
        patches: list[str] = []

        for path in paths_to_scan:
            PatchProvider.log.debug(f"Searching in '{path}'...")

            for item in path.iterdir():
                PatchProvider.log.debug(f"Checking item {str(item)!r}...")
                if not is_dir(item):
                    continue

                if item.match("*DIP*") and is_dir(item / "Patch"):
                    patches.append(str(item))

        PatchProvider.log.debug(f"Found {len(patches)} patches.")

        return patches
