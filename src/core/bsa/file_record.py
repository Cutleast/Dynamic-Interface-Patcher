"""
Copyright (c) Cutleast
"""

from io import BufferedReader

from .datatypes import Hash, Integer, String


class FileRecordBlock:
    """
    Class for file record block.
    """

    name: str
    file_records: list["FileRecord"]

    def parse(self, stream: BufferedReader, count: int):
        self.name = String.parse(stream, String.StrType.BZString)
        self.file_records = [FileRecord().parse(stream) for i in range(count)]

        return self

    def dump(self) -> bytes:
        data = b""

        data += String.dump(self.name, String.StrType.BZString)
        data += b"".join(file_record.dump() for file_record in self.file_records)

        return data


class FileRecord:
    """
    Class for file record.
    """

    name_hash: int
    size: int
    offset: int

    compressed: bool = None

    def has_compression_flag(self) -> bool:
        # Mask for the 30th bit (0x40000000)
        mask = 0x40000000

        # Use bitwise AND to check if the 30th bit is set
        is_set = self.size & mask

        return is_set != 0

    @staticmethod
    def apply_compression_flag(size: int) -> int:
        """
        Applies compression flag to `size`.
        """

        # Mask for the 30th bit (0x40000000)
        mask = 0x40000000

        # Use bitwise OR to set the 30th bit
        size |= mask

        return size

    def parse(self, stream: BufferedReader):
        self.name_hash = Hash.parse(stream)
        self.size = Integer.parse(stream, Integer.IntType.ULong)
        self.offset = Integer.parse(stream, Integer.IntType.ULong)

        return self

    def dump(self):
        data = b""

        data += Hash.dump(self.name_hash)
        if self.compressed:
            self.size = self.apply_compression_flag(self.size)
        data += Integer.dump(self.size, Integer.IntType.ULong)
        data += Integer.dump(self.offset, Integer.IntType.ULong)

        return data
