"""
Copyright (c) Cutleast
"""

import os
import struct
from enum import Enum, IntEnum, auto
from io import BufferedReader, BytesIO

from .utilities import read_data, get_stream


class Integer:
    """
    Class for all types of signed and unsigned integers.
    """

    class IntType(Enum):
        UInt8 = (1, False)
        """Unsigned Integer of size 1."""

        UInt16 = (2, False)
        """Unsigned Integer of size 2."""

        UInt32 = (4, False)
        """Unsigned Integer of size 4."""

        UInt64 = (8, False)
        """Unsigned Integer of size 8."""

        UShort = (2, False)
        """Same as UInt16."""

        ULong = (4, False)
        """Same as UInt32."""

        Int8 = (1, True)
        """Signed Integer of Size 1."""

        Int16 = (2, True)
        """Signed Integer of Size 2."""

        Int32 = (4, True)
        """Signed Integer of Size 4."""

        Int64 = (8, True)
        """Signed Integer of Size 8."""

        Short = (2, True)
        """Same as Int16."""

        Long = (4, True)
        """Same as Int32."""

    @staticmethod
    def parse(data: BufferedReader | bytes, type: IntType):
        size, signed = type.value

        return int.from_bytes(
            get_stream(data).read(size), byteorder="little", signed=signed
        )

    @staticmethod
    def dump(value: int, type: IntType):
        size, signed = type.value

        return value.to_bytes(size, byteorder="little", signed=signed)


class Float:
    """
    Class for all types of floats.
    """

    @staticmethod
    def parse(data: BufferedReader | bytes, size: int = 4) -> float:
        return struct.unpack("f", get_stream(data).read(size))[0]

    @staticmethod
    def dump(value: float, size: int = 4):
        return struct.pack("f", value)


class String:
    """
    Class for all types of chars and strings.
    """

    class StrType(Enum):
        Char = auto()
        """8-bit character."""

        WChar = auto()
        """16-bit character."""

        String = auto()
        """Not-terminated string."""

        WString = auto()
        """Not-terminated string prefixed by UInt16."""

        BZString = auto()
        """Null-terminated string prefixed by UInt8."""

        BString = auto()
        """Not-terminated string prefixed by UInt8."""

        List = auto()
        """List of strings separated by `\\x00`."""

    @staticmethod
    def parse(data: BufferedReader | bytes, type: StrType, size: int = None):
        stream = get_stream(data)

        match type:
            case type.Char:
                text = read_data(stream, 1)

            case type.WChar:
                text = read_data(stream, 2)

            case type.String:
                if size is None:
                    raise ValueError(
                        f"'size' must not be None when 'type' is 'String'!"
                    )

                text = read_data(stream, size)

            case type.WString:
                size = Integer.parse(stream, Integer.IntType.UInt16)
                text = read_data(stream, size)

            case type.BZString | type.BString:
                size = Integer.parse(stream, Integer.IntType.UInt8)
                text = read_data(stream, size).strip(b"\x00")

            case type.List:
                strings: list[str] = []

                while len(strings) < size:
                    string = b""
                    while (char := stream.read(1)) != b"\x00" and char:
                        string += char

                    if string:
                        strings.append(string.decode())

                return strings

        return text.decode()

    @staticmethod
    def dump(value: list[str] | str, type: StrType) -> bytes:
        match type:
            case type.Char | type.WChar | type.String:
                return value.encode()

            case type.WString:
                text = value.encode()
                size = Integer.dump(len(text), Integer.IntType.UInt16)
                return size + text

            case type.BString:
                text = value.encode()
                size = Integer.dump(len(text), Integer.IntType.UInt8)
                return size + text
            
            case type.BZString:
                text = value.encode() + b"\x00"
                size = Integer.dump(len(text), Integer.IntType.UInt8)
                return size + text

            case type.List:
                data = b"\x00".join(v.encode() for v in value) + b"\x00"

                return data


class Flags(IntEnum):
    """
    Class for all types of flags.
    """

    @classmethod
    def parse(
        cls, data: BufferedReader | bytes, type: Integer.IntType
    ) -> dict["Flags", bool]:
        # Convert the bytestring to an integer
        value = Integer.parse(data, type)

        parsed_flags = {}

        for flag in cls:
            parsed_flags[flag] = bool(value & flag.value)

        return parsed_flags

    @classmethod
    def dump(cls, flags: dict["Flags", bool], type: Integer.IntType) -> bytes:
        # Convert the parsed flags back into an integer
        value = 0
        for flag in cls:
            if flags.get(flag, False):
                value |= flag

        # Convert the integer back to a bytestring
        return Integer.dump(value, type)


class Hex:
    """
    Class for all types of hexadecimal strings.
    """

    @staticmethod
    def parse(data: BufferedReader | bytes, size: int):
        return read_data(data, size).hex()

    @staticmethod
    def dump(value: str, type: Integer.IntType):
        number = int(value, base=16)

        return Integer.dump(number, type)


class Hash:
    """
    Class for all types of hashes.
    """

    @staticmethod
    def parse(data: BufferedReader | bytes):
        return Integer.parse(data, Integer.IntType.UInt64)

    @staticmethod
    def dump(value: int):
        return Integer.dump(value, Integer.IntType.UInt64)

    @staticmethod
    def calc_hash(filename: str) -> int:
        """
        Returns TES4's two hash values for filename.
        Based on TimeSlips code, fixed for names < 3 characters
        and updated to Python 3.

        This original code is from here:
        https://en.uesp.net/wiki/Oblivion_Mod:Hash_Calculation
        """

        name, ext = os.path.splitext(
            filename.lower()
        )  # --"bob.dds" >> root = "bob", ext = ".dds"

        # Create the hashBytes array equivalent
        hash_bytes = [
            ord(name[-1]) if len(name) > 0 else 0,
            ord(name[-2]) if len(name) >= 3 else 0,
            len(name),
            ord(name[0]) if len(name) > 0 else 0,
        ]

        # Convert the byte array to a single 32-bit integer
        hash1: int = struct.unpack("I", bytes(hash_bytes))[0]

        # Apply extensions-specific bit manipulation
        if ext == ".kf":
            hash1 |= 0x80
        elif ext == ".nif":
            hash1 |= 0x8000
        elif ext == ".dds":
            hash1 |= 0x8080
        elif ext == ".wav":
            hash1 |= 0x80000000

        hash2 = 0
        for i in range(1, len(name) - 2):
            hash2 = hash2 * 0x1003F + ord(name[i])

        hash3 = 0
        for char in ext:
            hash3 = hash3 * 0x1003F + ord(char)

        uint_mask = 0xFFFFFFFF
        combined_hash = ((hash2 + hash3) & uint_mask) << 32 | hash1

        return combined_hash
