"""
Copyright (c) Cutleast
"""

import os
from io import BufferedReader, BytesIO
from pathlib import Path


def create_folder_list(folder: Path):
    """
    Creates a list with all files
    with relative paths to `folder` and returns it.
    """

    files: list[Path] = []

    for root, _, _files in os.walk(folder):
        for f in _files:
            path = os.path.join(root, f)
            files.append(Path(path).relative_to(folder.parent))

    return files


def get_stream(data: BufferedReader | bytes) -> BytesIO:
    if isinstance(data, bytes):
        return BytesIO(data)

    return data


def read_data(data: BufferedReader | bytes, size: int) -> bytes:
    """
    Returns `size` bytes from `data`.
    """

    if isinstance(data, bytes):
        return data[:size]
    else:
        return data.read(size)
