"""
Copyright (c) Cutleast
"""

from pydantic.dataclasses import dataclass


@dataclass
class PatchItem:
    """
    Dataclass representing a single patch item consisting of a filter (XPath) and a dict
    of attributes and values to set.
    """

    filter: str
    """The filter/path to the item to be patched."""

    changes: dict[str, str]
    """A dictionary of attributes and values to set."""
