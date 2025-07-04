"""
Copyright (c) Cutleast
"""

from enum import StrEnum


class PatchType(StrEnum):
    """
    Enum for supported patch types.
    """

    Binary = ".bin"
    """This patch is executed by xdelta."""

    Json = ".json"
    """This patch is executed by FFDec."""
