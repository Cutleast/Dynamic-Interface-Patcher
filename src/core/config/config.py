"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Optional

from ._base_config import BaseConfig


class Config(BaseConfig):
    """
    Class for managing settings.
    """

    def __init__(self, config_folder: Path):
        super().__init__(config_folder / "config.json")

    @property
    def debug_mode(self) -> bool:
        """
        Toggles whether debug files get outputted.
        """

        return self._settings["debug_mode"]

    @debug_mode.setter
    def debug_mode(self, value: bool):
        Config.validate_type(value, bool)

        self._settings["debug_mode"] = value

    @property
    def repack_bsas(self) -> bool:
        """
        Toggles whether to repack BSAs after patching.
        """

        return self._settings["repack_bsa"]

    @repack_bsas.setter
    def repack_bsas(self, value: bool):
        Config.validate_type(value, bool)

        self._settings["repack_bsa"] = value

    @property
    def silent(self) -> bool:
        """
        Toggles whether GUI is shown.
        """

        return self._settings["silent"]

    @silent.setter
    def silent(self, value: bool):
        Config.validate_type(value, bool)

        self._settings["silent"] = value

    @property
    def output_folder(self) -> Optional[Path]:
        """
        Specifies output path for patched files.
        """

        if self._settings["output_folder"] is not None:
            return Path(self._settings["output_folder"]).resolve()

    @output_folder.setter
    def output_folder(self, path: Path):
        Config.validate_type(path, Path)

        if not path.parent.is_dir():
            raise FileNotFoundError(path)
        elif path.is_file():
            raise NotADirectoryError(path)

        self._settings["output_folder"] = str(path.resolve())
