"""
Part of Dynamic Interface Patcher (DIP).
Contains FFDec (JPEXS Free Flash Decompiler) interface.

Licensed under Attribution-NonCommercial-NoDerivatives 4.0 International
"""

import logging
import subprocess
from pathlib import Path

import errors
from main import MainApp


class FFDec:
    """
    Class for FFDec commandline interface.
    """

    bin_path = (Path(".") / "assets" / "ffdec" / "ffdec.bat").resolve()
    swf_path = None
    pid: int = None

    symlink_path: Path | None = None

    def __init__(self, swf_path: Path, app: MainApp):
        self.app = app

        self.log = logging.getLogger(self.__repr__())

        self.swf_path = swf_path

    def __repr__(self):
        return "FFDecInterface"

    def _exec_command(self, args: str):
        cmd = f""""{self.bin_path}" {args}"""

        output = ""

        with subprocess.Popen(
            cmd,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf8",
            errors="ignore",
        ) as process:
            self.pid = process.pid
            for line in process.stdout:
                output += line

        self.pid = None

        if process.returncode:
            self.log.error(f"FFDec Command:\n{cmd}")
            self.log.error(f"FFDec Output:\n{output}")
            raise errors.FFDecError(
                "Failed to execute FFDec command! Check output above!"
            )

    def replace_shapes(self, shapes: dict[Path, list[int]]):
        """
        Replaces shapes in SWF by <shapes>.

        Params:
            shapes: dictionary, keys are svg paths and values are list with indexes
        """

        self.log.info(f"Patching shapes of file '{self.swf_path.name}'...")

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
                cmd = f"""{index}\n{shape}\n"""
                cmds.append(cmd)
        cmdfile = self.swf_path.parent / "shapes.txt"
        with open(cmdfile, "w", encoding="utf8") as file:
            file.writelines(cmds)

        cmd = f"""-replace "{self.swf_path}" "{self.swf_path}" "{cmdfile.resolve()}" """

        self._exec_command(cmd)

        self.log.info("Shapes patched.")

    def swf2xml(self):
        """
        Converts SWF file to XML file and returns file path.
        """

        self.log.info("Converting SWF to XML...")
        self.log.debug(f"File: {self.swf_path}")

        out_path = self.swf_path.with_suffix(".xml")

        args = f"""-swf2xml "{self.swf_path}" "{out_path}" """
        self._exec_command(args)

        self.log.info("Converted to XML.")

        return out_path

    def xml2swf(self, xml_file: Path):
        """
        Converts XML file to SWF file and returns file path.
        """

        self.log.info("Converting XML to SWF...")
        self.log.debug(f"File: {xml_file}")

        out_path = xml_file.with_suffix(".swf")

        args = f"""-xml2swf "{xml_file}" "{out_path}" """
        self._exec_command(args)

        self.log.info("Converted to SWF.")

        return out_path
