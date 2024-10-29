"""
Copyright (c) Cutleast
"""

import os
import sys
from pathlib import Path
from typing import Any, TextIO

from PySide6.QtCore import QObject, Signal


class StdoutHandler(QObject):
    """
    Redirector class for sys.stdout.

    Redirects sys.stdout to self.output_signal [QtCore.Signal].
    """

    output_signal: Signal = Signal(str)
    _stream: TextIO
    _content: str

    log_file: Path = Path(os.getcwd()) / "DIP.log"
    __file_stream: TextIO

    def __init__(self, parent: QObject) -> None:
        super().__init__(parent)

        self._stream = sys.stdout
        sys.stdout = self
        self._content = ""

        self.__prepare_log_file()

    def __prepare_log_file(self) -> None:
        self.log_file.write_text("", encoding="utf8")

        self.__file_stream = self.log_file.open("a", encoding="utf8")

    def write(self, text: str) -> None:
        if self._stream is not None:
            self._stream.write(text)

        self._content += text
        self.__file_stream.write(text)
        self.output_signal.emit(text)

    def close(self) -> None:
        try:
            self.__file_stream.close()
        except Exception:
            pass

    def __getattr__(self, name: str) -> Any:
        return getattr(self._stream, name)

    def __del__(self) -> None:
        self.close()

        try:
            sys.stdout = self._stream
        except AttributeError:
            pass
