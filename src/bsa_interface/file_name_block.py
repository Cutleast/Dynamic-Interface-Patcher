"""
Copyright (c) Cutleast
"""

import os
from io import BufferedReader

from .datatypes import String


class FileNameBlock:
    """
    Class for file name block.
    """

    file_names: list[str]

    def parse(self, stream: BufferedReader, count: int):
        self.file_names = String.parse(stream, String.StrType.List, count)

        return self

    def dump(self) -> bytes:
        data = String.dump(self.file_names, String.StrType.List)

        return data
