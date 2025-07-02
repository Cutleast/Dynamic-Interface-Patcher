"""
Copyright (c) Cutleast
"""

import logging
import os
import sys
from enum import StrEnum
from io import TextIOWrapper
from pathlib import Path
from typing import Any, Optional, TextIO, override

from PySide6.QtCore import QObject, Signal


class Logger(logging.Logger, QObject):
    """
    Class for application logging. Copies all logging messages from
    `sys.stdout` and `sys.stderr` to a file and executes a callback with the new message.
    """

    log_signal = Signal(str)
    """
    Signal that gets emitted for every log message written to stdout.

    Args:
        str: Log message
    """

    __lines: list[str]
    __root_logger: logging.Logger
    __log_handler: logging.StreamHandler

    __stdout: Optional[TextIO] = None
    __stderr: Optional[TextIO] = None

    __log_file_path: Path
    __log_file: TextIOWrapper

    class Level(StrEnum):
        """Enum for logging levels."""

        Debug = "DEBUG"
        """Debugging log level"""

        Info = "INFO"
        """Information log level"""

        Warning = "WARNING"
        """Warning log level"""

        Error = "ERROR"
        """Error log level"""

        Critical = "CRITICAL"
        """Critical log level"""

    def __init__(
        self, log_file: Path, fmt: str | None = None, date_fmt: str | None = None
    ) -> None:
        QObject.__init__(self)
        super().__init__("Logger")

        # Create log folder if it doesn't exist
        os.makedirs(log_file.parent, exist_ok=True)

        self.__log_file_path = log_file
        log_file.write_text("", encoding="utf8")  # clear log file
        self.__log_file = log_file.open("a", encoding="utf8")

        self.__root_logger = logging.getLogger()
        formatter = logging.Formatter(fmt, date_fmt)
        self.__log_handler = logging.StreamHandler(self)
        self.__log_handler.setFormatter(formatter)
        self.__root_logger.addHandler(self.__log_handler)
        self.addHandler(self.__log_handler)
        self.__lines = []

        self.open()

    def open(self) -> None:
        self.__stdout = sys.stdout
        self.__stderr = sys.stderr

        sys.stdout = self
        sys.stderr = self

    @override
    def setLevel(self, level: Level) -> None:  # type: ignore
        """
        Sets logging level.

        Args:
            level (Level): New logging level.
        """

        self.__root_logger.setLevel(level.value)
        self.__log_handler.setLevel(level.value)

        super().setLevel(level.value)

    def close(self) -> None:
        sys.stdout = self.__stdout
        sys.stderr = self.__stderr
        self.__log_file.close()

    def write(self, string: str) -> None:
        """
        Writes a string to stdout and calls callback with string as argument

        Args:
            string (str): Message.
        """

        try:
            self.__lines.append(string)
            self.__log_file.write(string)
            if self.__stdout is not None:
                self.__stdout.write(string)
        except Exception as ex:
            if self.__stdout is not None:
                self.__stdout.write(f"Logging error occured: {str(ex)}")

        self.log_signal.emit(string)

    def flush(self) -> None:
        """
        Flushes file.
        """

        self.__log_file.flush()

    def get_content(self) -> str:
        """
        Returns content of current log as string.

        Returns:
            str: Content of current log.
        """

        return "".join(self.__lines)

    def get_file_path(self) -> Path:
        """
        Returns path to current log file.

        Returns:
            Path: Path to current log file.
        """

        return self.__log_file_path

    @staticmethod
    def log_str_dict(logger: logging.Logger, string_dict: dict[str, Any]) -> None:
        """
        Prints the specified dictionary prettified and formatted to the specified logger
        with log level `Logger.Level.INFO`.

        Args:
            logger (logging.Logger): Logger to print to
            string_dict (dict[str, Any]): Dictionary to print
        """

        indent: int = max(len(key) + 1 for key in string_dict)
        for key, value in string_dict.items():
            logger.info(f"{key.rjust(indent)} = {value!r}")
