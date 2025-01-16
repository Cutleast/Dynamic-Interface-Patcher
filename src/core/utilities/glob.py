"""
Copyright (c) Cutleast

This module contains a workaround function for MO2 and Win 11 24H2.
See this issue for more information:
    https://github.com/ModOrganizer2/modorganizer/issues/2174
"""

import ctypes
from pathlib import Path

lib = ctypes.CDLL("./glob.dll")

ENCODING: str = "cp1252"
"""
The encoding used by the underlying C++ code.
"""

# Define function signatures
lib.glob_cpp.argtypes = [
    ctypes.POINTER(ctypes.c_char),
    ctypes.POINTER(ctypes.c_char),
    ctypes.c_bool,
    ctypes.POINTER(ctypes.c_size_t),
]
lib.glob_cpp.restype = ctypes.POINTER(ctypes.c_char_p)
lib.glob_clear.argtypes = []
lib.glob_clear.restype = None


def glob(path: Path, pattern: str, recursive: bool = True) -> list[Path]:
    """
    A glob.glob-like function that is implemented in C++ to workaround issues with MO2's
    VFS on Windows 11 24H2.

    Args:
        path (Path): Base path to search in.
        pattern (str): Glob pattern.
        recursive (bool, optional): Whether to search recursively. Defaults to True.

    Returns:
        list[str]: List of matching filenames
    """

    count = ctypes.c_size_t()

    encoded_path: bytes = str(path).encode(ENCODING)
    encoded_pattern: bytes = pattern.encode(ENCODING)

    result_ptr = lib.glob_cpp(
        encoded_pattern, encoded_path, recursive, ctypes.byref(count)
    )

    results: list[Path] = [
        Path(result_ptr[i].decode(ENCODING)) for i in range(count.value)
    ]

    return results
