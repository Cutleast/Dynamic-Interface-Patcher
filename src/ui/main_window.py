"""
Copyright (c) Cutleast
"""

import os

import qtawesome as qta
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QColor
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core.config.config import Config
from core.patcher.patcher import Patcher
from core.utilities.licenses import LICENSES
from core.utilities.logger import Logger

from .main_widget import MainWidget


class MainWindow(QMainWindow):
    """
    Class for main patcher window.
    """

    def __init__(self, logger: Logger, config: Config, patcher: Patcher):
        super().__init__()

        self.setCentralWidget(MainWidget(logger, config, patcher))
        self.resize(1000, 600)

        # Menu Bar
        help_menu = self.menuBar().addMenu("Help")

        about_action: QAction = help_menu.addAction("About")
        about_action.setIcon(qta.icon("fa5s.info-circle", color="#ffffff"))
        about_action.triggered.connect(self.about)

        about_qt_action: QAction = help_menu.addAction("About Qt")
        about_qt_action.triggered.connect(self.about_qt)

        # Fix link color
        palette = self.palette()
        palette.setColor(palette.ColorRole.Link, QColor("#4994e0"))
        self.setPalette(palette)

        docs_label = QLabel(
            "\
Interested in creating own patches? \
Read the documentation \
<a href='https://github.com/Cutleast/Dynamic-Interface-Patcher/blob/main/DOCUMENTATION.md'>\
here</a>.\
"
        )
        docs_label.setTextFormat(Qt.TextFormat.RichText)
        docs_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        docs_label.setOpenExternalLinks(True)
        self.statusBar().addPermanentWidget(docs_label)

    def about(self):
        """
        Displays about dialog.
        """

        dialog = QDialog(QApplication.activeModalWidget())
        dialog.setWindowTitle("About")

        vlayout = QVBoxLayout()
        dialog.setLayout(vlayout)

        tab_widget = QTabWidget()
        tab_widget.tabBar().setExpanding(True)
        tab_widget.setObjectName("centered_tab")
        vlayout.addWidget(tab_widget)

        about_tab = QWidget()
        about_tab.setObjectName("transparent")
        tab_widget.addTab(about_tab, "About")

        hlayout = QHBoxLayout()
        about_tab.setLayout(hlayout)

        hlayout.addSpacing(25)

        icon = self.windowIcon()
        pixmap = icon.pixmap(128, 128)
        icon_label = QLabel()
        icon_label.setPixmap(pixmap)
        hlayout.addWidget(icon_label)

        hlayout.addSpacing(15)

        vlayout = QVBoxLayout()
        hlayout.addLayout(vlayout, 1)

        hlayout.addSpacing(25)
        vlayout.addSpacing(25)

        title_label = QLabel(
            f"{QApplication.applicationName()} v{QApplication.applicationVersion()}"
        )
        title_label.setObjectName("title_label")
        vlayout.addWidget(title_label)

        text = """
Created by Cutleast (<a href='https://next.nexusmods.com/profile/Cutleast'>NexusMods</a> 
| <a href='https://github.com/cutleast'>GitHub</a> | <a href='https://ko-fi.com/cutleast'>Ko-Fi</a>)
<br><br>
Icon by Wuerfelhusten (<a href='https://next.nexusmods.com/profile/Wuerfelhusten'>NexusMods</a>)
<br><br>
Licensed under GNU General Public License v3.0
"""

        credits_label = QLabel(text)
        credits_label.setTextFormat(Qt.TextFormat.RichText)
        credits_label.setOpenExternalLinks(True)
        vlayout.addWidget(credits_label)

        vlayout.addSpacing(25)

        licenses_tab = QListWidget()
        tab_widget.addTab(licenses_tab, "Used Software")

        licenses_tab.addItems(list(LICENSES.keys()))

        licenses_tab.itemDoubleClicked.connect(
            lambda item: os.startfile(LICENSES[item.text()])
        )

        dialog.exec()

    def about_qt(self):
        """
        Displays about Qt dialog.
        """

        QMessageBox.aboutQt(QApplication.activeModalWidget(), "About Qt")
