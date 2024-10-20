"""
Copyright (c) Cutleast
"""

import pyperclip as clipboard
import qtawesome as qta
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QMessageBox, QPushButton, QWidget


class ErrorDialog(QMessageBox):
    """
    Custom error messagebox with short text and detailed text functionality.

    Args:
        parent (QWidget | None): Parent window. `None` sets active modal widget as parent.
        title (str): Window title.
        text (str): Short message.
        details (str, optional): Long message that is displayed when details are shown.
        yesno (bool, optional):
            Toggles 'Continue' and 'Cancel' buttons or only an 'ok' button. Defaults to True.
    """

    def __init__(
        self,
        parent: QWidget | None,
        title: str,
        text: str,
        details: str = "",
        yesno: bool = True,
    ):
        if parent is None:
            parent = QApplication.activeModalWidget()

        super().__init__(parent)

        # Basic configuration
        self.setWindowTitle(title)
        self.setIcon(QMessageBox.Icon.Critical)
        self.setText(text)

        icon_color = self.palette().text().color()

        # Show 'continue' and 'cancel' button
        if yesno:
            self.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            self.button(QMessageBox.StandardButton.Yes).setText("Continue")
            self.button(QMessageBox.StandardButton.No).setText("Exit")

        # Only show 'ok' button
        else:
            self.setStandardButtons(QMessageBox.StandardButton.Ok)

        # Add details button if details are given
        if details:
            self.details_button: QPushButton = self.addButton(
                "Show Details...", QMessageBox.ButtonRole.AcceptRole
            )
            self.details_button.setIcon(qta.icon("fa5s.chevron-down", color=icon_color))

            self.copy_button: QPushButton = self.addButton(
                "", QMessageBox.ButtonRole.YesRole
            )
            self.copy_button.setText("")
            self.copy_button.setIcon(qta.icon("mdi6.content-copy"))
            self.copy_button.clicked.disconnect()
            self.copy_button.clicked.connect(lambda: clipboard.copy(details))
            self.copy_button.clicked.connect(
                lambda: self.copy_button.setIcon(qta.icon("fa5s.check"))
            )

            self._details = False
            label: QLabel = self.findChild(QLabel)

            def toggle_details():
                # toggle details
                if not self._details:
                    self._details = True
                    self.details_button.setText("Hide Details...")
                    self.details_button.setIcon(
                        qta.icon("fa5s.chevron-up", color=icon_color)
                    )
                    self.setInformativeText(
                        f"<font><p style='font-family: Consolas;font-size: 12px'>{details}</p>"
                    )
                    label.setTextInteractionFlags(
                        Qt.TextInteractionFlag.TextSelectableByMouse
                    )
                    label.setCursor(Qt.CursorShape.IBeamCursor)
                else:
                    self._details = False
                    self.details_button.setText("Show Details...")
                    self.details_button.setIcon(
                        qta.icon("fa5s.chevron-down", color=icon_color)
                    )
                    self.setInformativeText("")
                    label.setTextInteractionFlags(
                        Qt.TextInteractionFlag.NoTextInteraction
                    )
                    label.setCursor(Qt.CursorShape.ArrowCursor)

                # update messagebox size
                self.adjustSize()

            self.details_button.clicked.disconnect()
            self.details_button.clicked.connect(toggle_details)
