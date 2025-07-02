"""
Copyright (c) Cutleast
"""

from argparse import Namespace
from pathlib import Path
from typing import Optional, Self, override

from pydantic import model_validator

from core.utilities.filesystem import is_dir

from ._base_config import BaseConfig


class Config(BaseConfig):
    """
    Class for managing settings.
    """

    debug_mode: bool = False
    """Toggles whether debug files get outputted."""

    repack_bsas: bool = False
    """Toggles whether to repack BSAs after patching."""

    silent: bool = False
    """Toggles whether GUI is shown."""

    output_folder: Optional[Path] = None
    """Specifies output path for patched files."""

    # Auto patch config
    auto_patch: bool = False
    """Whether to automatically run the configured patch on startup."""

    patch_path: Optional[Path] = None
    """Path to the patch."""

    original_path: Optional[Path] = None
    """Path to the original mod."""

    @model_validator(mode="after")
    def validate_output_folder(self) -> Self:
        """
        Validates that the output folder exists, if specified.

        Raises:
            FileNotFoundError: When the output folder is not None and does not exist.

        Returns:
            Self: Self
        """

        if self.output_folder is not None and not is_dir(self.output_folder.parent):
            raise FileNotFoundError("Output folder does not exist.")

        return self

    @model_validator(mode="after")
    def validate_auto_patch_config(self) -> Self:
        """
        Validates the config for the auto patch.

        Returns:
            Self: Self
        """

        if self.auto_patch and (self.patch_path is None or self.original_path is None):
            raise ValueError(
                "Patch path and original path must be specified for auto patch."
            )

        return self

    @override
    def apply_from_namespace(self, namespace: Namespace) -> None:
        debug_mode: Optional[bool] = getattr(namespace, "debug", None)
        if debug_mode is not None:
            self.debug_mode = debug_mode

        repack_bsas: Optional[bool] = getattr(namespace, "repack_bsas", None)
        if repack_bsas is not None:
            self.repack_bsas = repack_bsas

        silent: Optional[bool] = getattr(namespace, "silent", None)
        if silent is not None:
            self.silent = silent

        output_folder: Optional[str] = getattr(namespace, "output_path", None)
        if output_folder is not None:
            self.output_folder = Path(output_folder)

        # apply auto patch config
        patch_path: Optional[str] = getattr(namespace, "patchpath", None)
        if patch_path is not None:
            self.patch_path = Path(patch_path)

        original_path: Optional[str] = getattr(namespace, "originalpath", None)
        if original_path is not None:
            self.original_path = Path(original_path)

        if patch_path is not None or original_path is not None:
            self.auto_patch = True

    @override
    @staticmethod
    def get_config_name() -> str:
        return "config.json"
