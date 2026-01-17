"""
Copyright (c) Cutleast

This module contains workaround functions for MO2 and Win 11 24H2.
See this issue for more information:
    https://github.com/ModOrganizer2/modorganizer/issues/2174

Importing this module will also patch
- `os.makedirs()`
- `Path.is_file()`
"""

import os
from pathlib import Path

from cutleast_core_lib.core.utilities.process_runner import run_process
from PySide6.QtCore import QDir, QFile


def file_path_to_qpath(path: str | Path) -> QFile:
    """
    Creates a `QFile` from a file path.

    Args:
        path (str | Path): Path to file

    Returns:
        QFile: QFile object
    """

    return QFile(str(path))


def folder_path_to_qpath(path: str | Path) -> QDir:
    """
    Creates a `QDir` from a folder path.

    Args:
        path (str | Path): Path to folder

    Returns:
        QDir: QDir object
    """

    return QDir(str(path))


def is_dir(path: Path) -> bool:
    """
    Checks if a folder exists. Doesn't use `Path.is_dir()` since
    its known to be broken with Win 11 24H2.

    Args:
        path (Path): Path to check

    Returns:
        bool: True if the path exists, False otherwise
    """

    return folder_path_to_qpath(path).exists()


def is_file(path: Path) -> bool:
    """
    Checks if a file exists. Doesn't use `Path.is_file()` since
    its known to be broken with Win 11 24H2.

    Args:
        path (Path): Path to check

    Returns:
        bool: True if the path exists, False otherwise
    """

    qfile: QFile = file_path_to_qpath(path)

    return not is_dir(path) and qfile.exists()


def mkdir(path: Path) -> None:
    """
    Creates a directory. Doesn't use `Path.mkdir()` since
    its known to be broken with Win 11 24H2.

    Does nothing if the specified path is already an existing folder.

    Raises:
        FileExistsError: If the specified path is already a file

    Args:
        path (Path): Path to create
    """

    if not is_dir(path) and not is_file(path):
        run_process(["mkdir", str(path).replace("/", "\\")])
    elif is_file(path):
        raise FileExistsError(f"{str(path)!r} already exists!")


def __makedirs(path, *args, **kwargs) -> None:  # pyright: ignore[reportMissingParameterType]
    mkdir(Path(path))


os.makedirs = __makedirs


def __path_is_file(self: Path, *args, **kwargs) -> bool:  # pyright: ignore[reportMissingParameterType]
    return is_file(self)


Path.is_file = __path_is_file
