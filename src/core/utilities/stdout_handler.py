"""
Copyright (c) Cutleast
"""

import sys
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

    def __init__(self, parent: QObject) -> None:
        super().__init__(parent)

        self._stream = sys.stdout
        sys.stdout = self
        self._content = ""

    def write(self, text: str) -> None:
        if self._stream is not None:
            self._stream.write(text)

        self._content += text
        self.output_signal.emit(text)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._stream, name)

    def __del__(self) -> None:
        try:
            sys.stdout = self._stream
        except AttributeError:
            pass
