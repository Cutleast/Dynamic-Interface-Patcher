"""
Copyright (c) Cutleast
"""

from PySide6.QtGui import Qt
from PySide6.QtWidgets import QLabel, QStatusBar


class StatusBar(QStatusBar):
    """
    Status bar for main window.
    """

    DOCS_URL: str = "https://github.com/Cutleast/Dynamic-Interface-Patcher/blob/main/DOCUMENTATION.md"

    def __init__(self) -> None:
        super().__init__()

        docs_label = QLabel(
            self.tr(
                "Interested in creating own patches? Read the documentation "
                "<a href='{0}'>here</a>."
            ).format(StatusBar.DOCS_URL)
        )
        docs_label.setTextFormat(Qt.TextFormat.RichText)
        docs_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        docs_label.setOpenExternalLinks(True)
        self.addPermanentWidget(docs_label)
