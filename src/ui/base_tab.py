"""
Copyright (c) Cutleast
"""

from abc import abstractmethod
from typing import Optional

from cutleast_core_lib.core.utilities.thread import Thread
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget

from core.utilities.status_update import StatusUpdate


class BaseTab(QWidget):
    """
    Common base class for the patcher and the patch creator tab widgets.
    """

    status_signal = Signal(StatusUpdate)
    """
    Signal emitted everytime there is a status update.

    Args:
        StatusUpdate: The status update to reflect in the UI.
    """

    valid_signal = Signal(bool)
    """
    Signal emitted everytime the validation status of the user input changes.
    
    Args:
        bool: Whether the user input is valid.
    """

    _thread: Optional[Thread[float]] = None

    def __init__(self) -> None:
        super().__init__()

        self.setObjectName("transparent")

    @abstractmethod
    def run(self) -> None:
        """
        Runs the process of this widget.
        """

    @abstractmethod
    def cancel(self) -> None:
        """
        Cancels the currently running process, if any.
        """
