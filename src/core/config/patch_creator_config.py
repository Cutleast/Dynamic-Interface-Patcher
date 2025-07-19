"""
Copyright (c) Cutleast
"""

from argparse import Namespace
from typing import override

from pydantic import Field

from ._base_config import BaseConfig


class PatchCreatorConfig(BaseConfig):
    """
    Configuration for the patch creator.
    """

    file_blacklist: list[str] = Field(default_factory=list)
    """Files that are ignored. For example, files that are known to raise errors."""

    export_format: str = "svg"
    """Shape export format. Possible formats: svg, png, jpeg"""

    creation_whitelist: list[str] = Field(default_factory=list)
    """XML tags of elements that are created if element is missing in original XML"""

    list_tags: list[str] = Field(default_factory=list)
    """Tags of elements that contain multiple children of same type"""

    filter_whitelist: list[str] = Field(default_factory=list)
    """Attributes that are used as filters"""

    type_blacklist: list[str] = Field(default_factory=list)
    """Types that are ignored"""

    tag_blacklist: list[str] = Field(default_factory=list)
    """ XML tags that are ignored"""

    attr_blacklist: list[str] = Field(default_factory=list)
    """Attributes that are completely ignored"""

    shape_types: list[str] = Field(default_factory=list)
    """Shape types that are compared and exported"""

    @override
    def apply_from_namespace(self, namespace: Namespace) -> None:
        pass

    @override
    @staticmethod
    def get_config_name() -> str:
        return "patch_creator_config.json"
