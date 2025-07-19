"""
Copyright (c) Cutleast
"""

import logging
from pathlib import Path

from core.archive.archive import Archive
from core.utilities.exe_info import get_current_path
from core.utilities.filesystem import is_file
from core.utilities.glob import glob
from core.utilities.process_runner import run_process


class FFDecInterface:
    """
    Class for FFDec commandline interface.
    """

    log: logging.Logger = logging.getLogger("FFDecInterface")

    bin_path: Path = get_current_path() / "ffdec" / "ffdec.bat"
    jre_archive_path: Path = get_current_path() / "jre.7z"

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

            if not is_file(shape):
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

    def export_shapes(
        self, swf_file: Path, shape_ids: list[int], outpath: Path, format: str
    ) -> None:
        """
        Exports the specified shapes from the specified SWF file to the specified output
        folder with the specified format.

        Args:
            swf_file (Path): Path to SWF file.
            shape_ids (list[int]): List of shape ids to export.
            outpath (Path): Path to folder the shapes get exported to.
        """

        self.log.info(f"Exporting {len(shape_ids)} shape(s) from '{swf_file}'...")

        cmd: list[str] = [
            str(self.bin_path),
            "-format",
            "shape:" + format,
            "-selectid",
            ",".join(list(map(str, shape_ids))),
            "-export",
            "shape",
            str(outpath),
            str(swf_file),
        ]
        run_process(cmd)

        self.log.info(f"Shape(s) exported to '{outpath}'.")

    def setup_jre(self, temp_folder: Path) -> None:
        """
        Extracts Java Runtime from jre.7z to the specified folder and redirects FFDec to
        it.

        Args:
            temp_folder (Path): Folder to extract Java Runtime to
        """

        self.log.info("Extracting Java Runtime from jre.7z...")

        archive: Archive = Archive.load_archive(self.jre_archive_path)

        if not archive.glob("*/bin/java.exe"):
            raise Exception("Archive does not contain a valid java.exe!")

        archive.extract_all(temp_folder)
        java_path: Path = list(glob(temp_folder, "java.exe"))[0]

        self.log.info(f"Java Runtime extracted to '{java_path}'.")
        self.log.info("Setting up FFDec...")

        # Write jre_path in ffdec.bat
        ffdec_bat_path = self.bin_path
        orig_bat_path = ffdec_bat_path.with_stem("ffdec_orig")

        text = orig_bat_path.read_text()
        lines = text.splitlines()
        last_line = lines[-1]

        last_line = last_line.replace("java", f'"{java_path}"', 1)
        lines[-1] = last_line

        ffdec_bat_path.write_text("\n".join(lines))

        self.log.info("FFDec setup complete.")
