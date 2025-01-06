"""
Copyright (c) Cutleast

This module contains workaround functions for MO2 and Win 11 24H2.
See this issue for more information:
    https://github.com/ModOrganizer2/modorganizer/issues/2174
"""

import os
from pathlib import Path


def is_dir(path: Path) -> bool:
    """
    Checks if a folder exists. Doesn't use `Path.is_dir()` since
    its known to be broken with Win 11 24H2.

    Args:
        path (Path): Path to check

    Returns:
        bool: True if the path exists, False otherwise
    """

    try:
        path.iterdir()
    except FileNotFoundError:
        return False

    return True


def is_file(path: Path) -> bool:
    """
    Checks if a file exists. Doesn't use `Path.is_file()` since
    its known to be broken with Win 11 24H2.

    Args:
        path (Path): Path to check

    Returns:
        bool: True if the path exists, False otherwise
    """

    try:
        os.stat(path)
    except FileNotFoundError:
        return False

    return True


def glob(base_path: str, pattern: str) -> list[Path]:
    """
    Custom implementation of `pathlib.Path.glob()` since
    its known to be broken with Win 11 24H2.

    Args:
        base_path (str): The path to the base directory to search in.
        pattern (str): The glob pattern to match (e.g., '*.json', '*.bin').

    Returns:
        list[Path]: A list of pathlib.Path objects that match the given pattern.
    """

    base_dir = Path(base_path)

    if not is_dir(base_dir):
        return []

    matched_files: list[Path] = []
    for item in base_dir.iterdir():
        if item.match(pattern):
            matched_files.append(item)

    return matched_files
