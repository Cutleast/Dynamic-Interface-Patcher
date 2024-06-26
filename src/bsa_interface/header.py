"""
Copyright (c) Cutleast
"""

from io import BufferedReader

from .datatypes import Flags, Integer


class Header:
    """
    Class for archive header.
    """

    class ArchiveFlags(Flags):
        IncludeDirectoryNames = 0x1
        IncludeFileNames = 0x2
        CompressedArchive = 0x4
        RetainDirectoryNames = 0x8
        RetainFileNames = 0x10
        RetainFileNameOffsets = 0x20
        Xbox360archive = 0x40
        RetainStringsDuringStartup = 0x80
        EmbedFileNames = 0x100
        XMemCodec = 0x200

    class FileFlags(Flags):
        Meshes = 0x1
        Textures = 0x2
        Menus = 0x4
        Sounds = 0x8
        Voices = 0x10
        Shaders = 0x20
        Trees = 0x40
        Fonts = 0x80
        Miscellaneous = 0x100

    file_id: bytes = b"BSA\x00"
    version: int = 0x69  # Skyrim SE as default version
    offset: int = 0x24  # Header has fix size of 36 bytes
    archive_flags: dict[ArchiveFlags, bool] = {
        ArchiveFlags.IncludeDirectoryNames: True,
        ArchiveFlags.IncludeFileNames: True,
        ArchiveFlags.CompressedArchive: True,
        ArchiveFlags.RetainDirectoryNames: True,
        ArchiveFlags.RetainFileNames: True,
        ArchiveFlags.RetainFileNameOffsets: True,
        ArchiveFlags.Xbox360archive: False,
        ArchiveFlags.RetainStringsDuringStartup: False,
        ArchiveFlags.EmbedFileNames : False,
        ArchiveFlags.XMemCodec : False,
    }
    folder_count: int
    file_count: int
    total_folder_name_length: int
    total_file_name_length: int
    file_flags: dict[str, bool] = {
        FileFlags.Meshes: False,
        FileFlags.Textures: False,
        FileFlags.Menus: False,
        FileFlags.Sounds: False,
        FileFlags.Voices: False,
        FileFlags.Shaders: False,
        FileFlags.Trees: False,
        FileFlags.Fonts: False,
        FileFlags.Miscellaneous: False,
    }
    padding: int = 0

    def parse(self, stream: BufferedReader):
        self.file_id = stream.read(4)
        self.version = Integer.parse(stream, Integer.IntType.ULong)

        if self.version != 105:
            raise Exception("Archive format is not supported!")

        self.offset = Integer.parse(stream, Integer.IntType.ULong)
        self.archive_flags = Header.ArchiveFlags.parse(stream, Integer.IntType.ULong)
        self.folder_count = Integer.parse(stream, Integer.IntType.ULong)
        self.file_count = Integer.parse(stream, Integer.IntType.ULong)
        self.total_folder_name_length = Integer.parse(stream, Integer.IntType.ULong)
        self.total_file_name_length = Integer.parse(stream, Integer.IntType.ULong)
        self.file_flags = Header.FileFlags.parse(stream, Integer.IntType.UShort)
        self.padding = Integer.parse(stream, Integer.IntType.UShort)

        return self

    def dump(self):
        data = b""

        data += self.file_id
        data += Integer.dump(self.version, Integer.IntType.ULong)
        data += Integer.dump(self.offset, Integer.IntType.ULong)
        data += Header.ArchiveFlags.dump(self.archive_flags, Integer.IntType.ULong)
        data += Integer.dump(self.folder_count, Integer.IntType.ULong)
        data += Integer.dump(self.file_count, Integer.IntType.ULong)
        data += Integer.dump(self.total_folder_name_length, Integer.IntType.ULong)
        data += Integer.dump(self.total_file_name_length, Integer.IntType.ULong)
        data += Header.FileFlags.dump(self.file_flags, Integer.IntType.UShort)
        data += Integer.dump(self.padding, Integer.IntType.UShort)

        return data
