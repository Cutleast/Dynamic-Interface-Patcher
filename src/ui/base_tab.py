"""
Copyright (c) Cutleast
"""

from abc import abstractmethod

from PySide6.QtWidgets import QWidget


class BaseTab(QWidget):
    """
    Common base class for the patcher and the patch creator tab widgets.
    """

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
