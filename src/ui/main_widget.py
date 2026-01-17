"""
Copyright (c) Cutleast
"""

import logging
from typing import override

from cutleast_core_lib.core.utilities.logger import Logger
from cutleast_core_lib.ui.widgets.copy_button import CopyButton
from PySide6.QtCore import Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.config.config import Config
from core.config.patch_creator_config import PatchCreatorConfig
from core.patch_creator.patch_creator import PatchCreator
from core.patcher.patcher import Patcher
from core.utilities.status_update import StatusUpdate

from .base_tab import BaseTab
from .patch_creator_widget import PatchCreatorWidget
from .patcher_widget import PatcherWidget


class MainWidget(QWidget):
    """
    Class for main widget.
    """

    log: logging.Logger = logging.getLogger("MainWidget")

    logger: Logger
    config: Config
    patch_creator_config: PatchCreatorConfig
    patcher: Patcher
    patch_creator: PatchCreator

    __vlayout: QVBoxLayout

    __tab_widget: QTabWidget
    __patcher_widget: PatcherWidget
    __patch_creator_widget: PatchCreatorWidget
    __protocol_widget: QTextEdit
    __progress_bar: QProgressBar
    __run_button: QPushButton

    log_signal = Signal(str)
    incr_progress_signal = Signal()

    def __init__(
        self,
        logger: Logger,
        config: Config,
        patch_creator_config: PatchCreatorConfig,
        patcher: Patcher,
        patch_creator: PatchCreator,
    ) -> None:
        super().__init__()

        self.logger = logger
        self.config = config
        self.patch_creator_config = patch_creator_config
        self.patcher = patcher
        self.patch_creator = patch_creator

        self.__init_ui()

        self.__patcher_widget.status_signal.connect(self.__handle_status_update)
        self.__patch_creator_widget.status_signal.connect(self.__handle_status_update)
        self.logger.set_callback(self.log_signal.emit)
        self.log_signal.connect(self.__handle_log_message)
        self.incr_progress_signal.connect(
            lambda: self.__progress_bar.setValue(self.__progress_bar.value() + 1)
        )

        if (
            self.config.auto_patch
            and self.config.patch_path is not None
            and self.config.original_path is not None
        ):
            self.log.info("Patching automatically...")
            self.__patcher_widget.run()

    def __init_ui(self) -> None:
        self.__vlayout = QVBoxLayout()
        self.setLayout(self.__vlayout)

        self.__init_header()
        self.__init_protocol_widget()
        self.__init_progress_bar()
        self.__init_footer()

    def __init_header(self) -> None:
        self.__tab_widget = QTabWidget()
        self.__tab_widget.tabBar().setExpanding(True)
        self.__tab_widget.tabBar().setDocumentMode(True)
        self.__vlayout.addWidget(self.__tab_widget)

        self.__patcher_widget = PatcherWidget(self.config, self.patcher)
        self.__tab_widget.addTab(self.__patcher_widget, "Patcher")

        self.__patch_creator_widget = PatchCreatorWidget(
            self.config, self.patch_creator_config, self.patch_creator
        )
        self.__tab_widget.addTab(self.__patch_creator_widget, "Patch Creator")

    def __init_protocol_widget(self) -> None:
        self.__protocol_widget = QTextEdit()
        self.__protocol_widget.setReadOnly(True)
        self.__protocol_widget.setObjectName("monospace")
        self.__handle_log_message(self.logger.get_content())
        self.__vlayout.addWidget(self.__protocol_widget, 1)

    def __init_progress_bar(self) -> None:
        self.__progress_bar = QProgressBar()
        self.__progress_bar.setRange(0, 1)
        self.__progress_bar.setTextVisible(False)
        self.__progress_bar.setFixedHeight(4)
        self.__vlayout.addWidget(self.__progress_bar)

    def __init_footer(self) -> None:
        hlayout = QHBoxLayout()
        self.__vlayout.addLayout(hlayout)

        self.__run_button = QPushButton("Run!")
        self.__run_button.setObjectName("primary")
        self.__run_button.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self.__run_button.clicked.connect(self.__run)
        self.__patcher_widget.valid_signal.connect(self.__run_button.setEnabled)
        hlayout.addWidget(self.__run_button)

        copy_log_button = CopyButton()
        copy_log_button.setToolTip("Copy Log to Clipboard")
        copy_log_button.clicked.connect(
            lambda: QApplication.clipboard().setText(
                self.__protocol_widget.toPlainText()
            )
        )
        hlayout.addWidget(copy_log_button)

    def __handle_log_message(self, text: str) -> None:
        self.__protocol_widget.insertPlainText(text)
        self.__protocol_widget.moveCursor(QTextCursor.MoveOperation.End)

    def __run(self) -> None:
        current_widget: QWidget = self.__tab_widget.currentWidget()

        if isinstance(current_widget, BaseTab):
            current_widget.run()

    def __cancel(self) -> None:
        current_widget: QWidget = self.__tab_widget.currentWidget()

        if isinstance(current_widget, BaseTab):
            current_widget.cancel()

    def __handle_status_update(self, status_update: StatusUpdate) -> None:
        match status_update:
            case StatusUpdate.Running:
                self.__progress_bar.setRange(0, 0)
                self.__progress_bar.setProperty("failed", False)

                self.__run_button.setText("Cancel")
                self.__run_button.setObjectName("")
                self.__run_button.clicked.disconnect()
                self.__run_button.clicked.connect(self.__cancel)

                self.__tab_widget.setDisabled(True)

            case StatusUpdate.Successful | StatusUpdate.Ready | StatusUpdate.Failed:
                self.__progress_bar.setRange(0, 1)
                self.__progress_bar.setValue(1)

                if status_update == StatusUpdate.Failed:
                    self.__progress_bar.setProperty("failed", True)

                self.__run_button.setText("Run!")
                self.__run_button.setObjectName("primary")
                self.__run_button.clicked.disconnect()
                self.__run_button.clicked.connect(self.__run)

                self.__tab_widget.setDisabled(False)

        self.update()

    @override
    def update(self) -> None:  # type: ignore
        self.style().unpolish(self)
        self.style().polish(self)

        self.__progress_bar.style().unpolish(self.__progress_bar)
        self.__progress_bar.style().polish(self.__progress_bar)

        self.__run_button.style().unpolish(self.__run_button)
        self.__run_button.style().polish(self.__run_button)

        super().update()
