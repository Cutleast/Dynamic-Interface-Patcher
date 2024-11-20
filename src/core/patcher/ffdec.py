"""
Copyright (c) Cutleast
"""

import logging
from pathlib import Path

from PySide6.QtWidgets import QApplication

from core.utilities.process_runner import run_process


class FFDecInterface:
    """
    Class for FFDec commandline interface.
    """

    log: logging.Logger = logging.getLogger("FFDecInterface")
    bin_path: Path

    def __init__(self):
        self.bin_path = QApplication.instance().app_path / "ffdec" / "ffdec.bat"

    def replace_shapes(self, swf_file: Path, shapes: dict[Path, list[int]]) -> None:
        """
        Replaces shapes in an SWF file.

        Args:
            swf_file (Path): Path to SWF file
            shapes (dict[Path, list[int]]): Dictionary mapping SVG paths and list of indexes
        """

        self.log.info(f"Patching shapes of file {swf_file.name!r}...")

        cmds: list[str] = []
        for shape, indexes in shapes.items():
            shape = shape.resolve()

            if not shape.is_file():
                self.log.error(
                    f"Failed to patch shape {shape.name}: File does not exist!"
                )
                continue

            if shape.suffix not in [".svg", ".png", ".jpg", ".jpeg"]:
                self.log.warning(
                    f"File type '{shape.suffix}' ({shape.name}) is not supported or tested and may lead to issues!"
                )

            for index in indexes:
                line = f"""{index}\n{shape}\n"""
                cmds.append(line)

        cmdfile: Path = swf_file.parent / "shapes.txt"
        with open(cmdfile, "w", encoding="utf8") as file:
            file.writelines(cmds)

        cmd: list[str] = [
            str(self.bin_path),
            "-replace",
            str(swf_file),
            str(swf_file),
            str(cmdfile.resolve()),
        ]
        run_process(cmd)

        self.log.info("Shapes patched.")

    def swf2xml(self, swf_file: Path) -> Path:
        """
        Converts an SWF file to an XML file.

        Args:
            swf_file (Path): SWF file to convert to XML.

        Returns:
            Path: to converted XML file.
        """

        self.log.info(f"Converting {swf_file.name!r} to XML...")

        out_path: Path = swf_file.with_suffix(".xml")

        cmd: list[str] = [
            str(self.bin_path),
            "-swf2xml",
            str(swf_file),
            str(out_path),
        ]
        run_process(cmd)

        self.log.info("Converted to XML.")

        return out_path

    def xml2swf(self, xml_file: Path) -> Path:
        """
        Converts an XML file to an SWF file.

        Args:
            xml_file (Path): XML file to convert to SWF.

        Returns:
            Path: to converted SWF file.
        """

        self.log.info(f"Converting {xml_file.name!r} to SWF...")

        out_path: Path = xml_file.with_suffix(".swf")

        cmd: list[str] = [
            str(self.bin_path),
            "-xml2swf",
            str(xml_file),
            str(out_path),
        ]
        run_process(cmd)

        self.log.info("Converted to SWF.")

        return out_path
