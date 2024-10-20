"""
Copyright (c) Cutleast
"""

from io import BufferedReader

from .datatypes import Hash, Integer


class FolderRecord:
    """
    Class for folder records.
    """

    name_hash: int
    count: int
    padding: int = 0
    offset: int
    padding2: int = 0

    def parse(self, stream: BufferedReader):
        self.name_hash = Hash.parse(stream)
        self.count = Integer.parse(stream, Integer.IntType.ULong)
        self.padding = Integer.parse(stream, Integer.IntType.ULong)
        self.offset = Integer.parse(stream, Integer.IntType.ULong)
        self.padding2 = Integer.parse(stream, Integer.IntType.ULong)

        return self

    def dump(self) -> bytes:
        data = b""

        data += Hash.dump(self.name_hash)
        data += Integer.dump(self.count, Integer.IntType.ULong)
        data += Integer.dump(self.padding, Integer.IntType.ULong)
        data += Integer.dump(self.offset, Integer.IntType.ULong)
        data += Integer.dump(self.padding2, Integer.IntType.ULong)

        return data
