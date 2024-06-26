"""
Copyright (c) Cutleast
"""

import os
from io import BytesIO
from pathlib import Path

import lz4.frame
from virtual_glob import InMemoryPath, glob

from .datatypes import Hash, Integer, String
from .file_name_block import FileNameBlock
from .file_record import FileRecord, FileRecordBlock
from .folder_record import FolderRecord
from .header import Header
from .utilities import create_folder_list


class BSAArchive:
    """
    Contains parsed archive data.
    """

    def __init__(self, archive_path: Path):
        self.path = archive_path

        self.parse()

    def match_names(self):
        """
        Matches file names to their records.
        """

        result: dict[str, FileRecord] = {}

        index = 0
        for file_record_block in self.file_record_blocks:
            for file_record in file_record_block.file_records:
                # result[self.file_name_block.file_names[index]] = file_record
                file_path = file_record_block.name
                file_name = self.file_name_block.file_names[index]
                file = str(Path(file_path) / file_name).replace("\\", "/")
                result[file] = file_record
                index += 1

        return result

    def process_compression_flags(self):
        """
        Processes compression flags in files.
        """

        for file_record in self.files.values():
            has_compression_flag = file_record.has_compression_flag()
            compressed_archive = self.header.archive_flags[
                self.header.ArchiveFlags.CompressedArchive
            ]

            if has_compression_flag:
                file_record.compressed = not compressed_archive
            else:
                file_record.compressed = compressed_archive

    def parse(self):
        with self.path.open("rb") as stream:
            self.header = Header().parse(stream)
            self.folders = [
                FolderRecord().parse(stream) for i in range(self.header.folder_count)
            ]
            self.file_record_blocks = [
                FileRecordBlock().parse(stream, self.folders[i].count)
                for i in range(self.header.folder_count)
            ]
            self.file_name_block = FileNameBlock().parse(stream, self.header.file_count)

        self.files = self.match_names()
        self.process_compression_flags()

        return self

    def glob(self, pattern: str):
        """
        Returns a list of file paths that
        match the <pattern>.

        Parameters:
            pattern: str, everything that fnmatch supports

        Returns:
            list of matching filenames
        """

        fs = InMemoryPath.from_list(list(self.files.keys()))
        matches = [p.path for p in glob(fs, pattern)]

        return matches

    def extract(self, dest_folder: Path):
        """
        Extracts archive content to `dest_folder`.
        """

        for file in self.files:
            self.extract_file(file, dest_folder)

    def extract_file(self, filename: str | Path, dest_folder: Path):
        """
        Extracts `filename` from archive to `dest_folder`.
        """

        filename = str(filename).replace("\\", "/")

        if filename not in self.files:
            raise FileNotFoundError(f"{filename!r} is not in archive!")

        file_record = self.files[filename]

        # Go to file raw data
        with self.path.open("rb") as stream:
            stream.seek(file_record.offset)

            file_size = file_record.size

            if self.header.archive_flags[self.header.ArchiveFlags.EmbedFileNames]:
                filename = String.parse(stream, String.StrType.BString)
                file_size -= (
                    len(filename) + 1
                )  # Subtract file name length + Uint8 prefix

            if file_record.compressed:
                original_size = Integer.parse(stream, Integer.IntType.ULong)
                data = stream.read(file_size - 4)
                data = lz4.frame.decompress(data)
            else:
                data = stream.read(file_size)

        destination = dest_folder / filename
        os.makedirs(destination.parent, exist_ok=True)
        with open(destination, "wb") as file:
            file.write(data)

        if not destination.is_file():
            raise Exception(
                f"Failed to extract file '{filename}' from archive '{self.path}'!"
            )

    def get_file_stream(self, filename: str | Path):
        """
        Instead of extracting the file this returns a file stream to the file data.
        """

        filename = str(filename)

        if filename not in self.files:
            raise FileNotFoundError("File is not in archive!")

        file_record = self.files[filename]

        with self.path.open("rb") as stream:
            # Go to file raw data
            stream.seek(file_record.offset)

            file_size = file_record.size

            if self.header.archive_flags[self.header.ArchiveFlags.EmbedFileNames]:
                filename = String.parse(stream, String.StrType.BString)
                file_size -= (
                    len(filename) + 1
                )  # Subtract file name length + Uint8 prefix

            if file_record.compressed:
                original_size = Integer.parse(stream, Integer.IntType.ULong)
                data = stream.read(file_size - 4)
                data = lz4.frame.decompress(data)
            else:
                data = stream.read(file_size)

        return BytesIO(data)

    @staticmethod
    def create_file_flags(folders: list[Path]):
        file_flags: dict[Header.FileFlags, bool] = {}

        for folder in folders:
            root_folder_name = folder.parts[0].lower()
            sub_folder_name = folder.parts[1].lower() if len(folder.parts) > 1 else None

            match root_folder_name:
                case "meshes":
                    file_flags[Header.FileFlags.Meshes] = True
                case "textures":
                    file_flags[Header.FileFlags.Textures] = True
                case "interface":
                    file_flags[Header.FileFlags.Menus] = True
                case "sounds":
                    file_flags[Header.FileFlags.Sounds] = True
                    if sub_folder_name == "voice":
                        file_flags[Header.FileFlags.Voices] = True

                case _:
                    file_flags[Header.FileFlags.Miscellaneous] = True

        return file_flags

    @staticmethod
    def create_archive(
        input_folder: Path,
        output_file: Path,
        archive_flags: dict[Header.ArchiveFlags, bool] = None,
        file_flags: dict[Header.FileFlags, bool] = None,
    ):
        """
        Creates an archive from `input_folder`.
        """

        if not input_folder.is_dir():
            raise ValueError(f"{str(input_folder)!r} must be an existing directory!")

        # Get elements and prepare folder and file structure
        files: list[Path] = []
        for element in os.listdir(input_folder):
            if os.path.isdir(input_folder / element):
                files += create_folder_list(input_folder / element)
        file_name_block = FileNameBlock()
        file_name_block.file_names = [file.name for file in files]
        folders: dict[Path, list[Path]] = {}
        for file in files:
            folder = file.parent

            if folder in folders:
                folders[folder].append(file)
            else:
                folders[folder] = [file]

        if not folders or not file_name_block.file_names:
            raise Exception("No elements to pack!")

        # Create header
        header = Header()
        header.file_count = len(files)
        header.folder_count = len(folders)
        header.total_file_name_length = len(file_name_block.dump())
        header.total_folder_name_length = len(
            String.dump([str(folder) for folder in folders], String.StrType.List)
        )
        header.file_flags = BSAArchive.create_file_flags(list(folders.keys()))

        if archive_flags is not None:
            header.archive_flags.update(archive_flags)
        if file_flags is not None:
            header.file_flags.update(file_flags)

        if (
            header.archive_flags[Header.ArchiveFlags.EmbedFileNames]
            and header.archive_flags[Header.ArchiveFlags.CompressedArchive]
        ):
            print(
                "WARNING! Use Embedded File Names and Compresion at the same time at your own risk!"
            )

        # Create record and block structure
        folder_records: list[FolderRecord] = []
        file_record_blocks: list[FileRecordBlock] = []
        file_records: dict[FileRecord, str] = {}
        current_offset = 36  # Start with header size
        current_offset += len(folders) * 24  # Add estimated size of all folder records

        for folder, _files in folders.items():
            folder_name = str(folder).replace("/", "\\")

            folder_record = FolderRecord()
            folder_record.name_hash = Hash.calc_hash(folder_name)
            folder_record.count = len(_files)
            folder_record.offset = current_offset
            folder_records.append(folder_record)

            file_record_block = FileRecordBlock()
            file_record_block.name = folder_name
            file_record_block.file_records = []

            for file in _files:
                file_record = FileRecord()
                file_record.name_hash = Hash.calc_hash(file.name.lower())
                file_record.size = os.path.getsize(input_folder / file)
                file_records[file_record] = str(file).replace("/", "\\")
                file_record_block.file_records.append(file_record)

            # Add name length of file record block (+ Uint8 and null-terminator)
            current_offset += len(file_record_block.name) + 2
            # Add estimated size of all file records from current file record block
            current_offset += len(file_record_block.file_records) * 16

            file_record_blocks.append(file_record_block)

        current_offset += len(file_name_block.dump())  # Add size of file name block

        # Write file
        with output_file.open("wb") as output_stream:
            # Write Placeholder for Record Structure
            output_stream.write(b"\x00" * current_offset)

            for file_record, file_name in file_records.items():
                if header.archive_flags[Header.ArchiveFlags.EmbedFileNames]:
                    output_stream.write(String.dump(file_name, String.StrType.BString))
                    file_record.size += len(file_name) + 1

                if header.archive_flags[Header.ArchiveFlags.CompressedArchive]:
                    with (input_folder / file_name).open("rb") as file:
                        data = file.read()

                    compressed_data: bytes = lz4.frame.compress(data)

                    output_stream.write(
                        Integer.dump(file_record.size, Integer.IntType.ULong)
                    )
                    output_stream.write(compressed_data)
                    file_record.size = (
                        len(compressed_data) + 4
                    )  # Compressed size + ULong prefix

                    # Readd file name length after reducing file size to compressed size
                    if header.archive_flags[Header.ArchiveFlags.EmbedFileNames]:
                        file_record.size += len(file_name) + 1
                else:
                    with (input_folder / file_name).open("rb") as file:
                        while data := file.read(1024 * 1024):
                            output_stream.write(data)

            # Calculate file offsets
            for file_record, file_name in file_records.items():
                file_record.offset = current_offset
                current_offset += file_record.size  # Add file size

            output_stream.seek(0)
            output_stream.write(header.dump())
            output_stream.write(
                b"".join(folder_record.dump() for folder_record in folder_records)
            )
            output_stream.write(
                b"".join(
                    file_record_block.dump() for file_record_block in file_record_blocks
                )
            )
            output_stream.write(file_name_block.dump())
