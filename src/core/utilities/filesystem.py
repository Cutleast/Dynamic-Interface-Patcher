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
        list(path.iterdir())
    except (FileNotFoundError, NotADirectoryError):
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
