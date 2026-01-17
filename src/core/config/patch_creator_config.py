"""
Copyright (c) Cutleast
"""

from typing import override

from cutleast_core_lib.core.config.base_config import BaseConfig
from pydantic import Field


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
    @staticmethod
    def get_config_name() -> str:
        return "patch_creator_config.json"
