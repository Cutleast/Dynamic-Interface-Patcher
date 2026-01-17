"""
Copyright (c) Cutleast
"""

import logging
import os
from pathlib import Path

from cutleast_core_lib.core.utilities.exe_info import get_current_path
from cutleast_core_lib.core.utilities.process_runner import run_process


class XDeltaInterface:
    """
    Class for xdelta commandline interface.
    """

    log: logging.Logger = logging.getLogger("xdelta")
    bin_path: Path = get_current_path() / "res" / "xdelta" / "xdelta.exe"

    def patch_file(self, original_file_path: Path, xdelta_file_path: Path) -> None:
        self.log.info(f"Patching {original_file_path.name!r} with xdelta...")

        output_file_path: Path = original_file_path.with_suffix(".patched")
        cmd: list[str] = [
            str(self.bin_path),
            "-d",
            "-s",
            str(original_file_path),
            str(xdelta_file_path),
            str(output_file_path),
        ]
        self.log.debug(" ".join(cmd))
        run_process(cmd)

        os.remove(original_file_path)
        os.rename(output_file_path, original_file_path)

        self.log.info(f"{original_file_path.name!r} patched.")
