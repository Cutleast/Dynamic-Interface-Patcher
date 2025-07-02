"""
Copyright (c) Cutleast
"""

import qtawesome as qta
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

from core.utilities.status_update import StatusUpdate
from core.utilities.stdout_handler import StdoutHandler

from .patcher_widget import PatcherWidget


class MainWidget(QWidget):
    """
    Class for main widget.
    """

    tab_widget: QTabWidget
    patcher_widget: PatcherWidget

    vlayout: QVBoxLayout

    incr_progress_signal = Signal()

    def __init__(self):
        super().__init__()

        self.__init_ui()

        self.patcher_widget.status_signal.connect(self.__handle_status_update)

    def __init_ui(self) -> None:
        self.vlayout = QVBoxLayout()
        self.setLayout(self.vlayout)

        self.__init_header()
        self.__init_protocol_widget()
        self.__init_progress_bar()
        self.__init_footer()

    def __init_header(self) -> None:
        self.tab_widget = QTabWidget()
        self.tab_widget.tabBar().setExpanding(True)
        self.tab_widget.tabBar().setDocumentMode(True)
        self.vlayout.addWidget(self.tab_widget)

        self.patcher_widget = PatcherWidget()
        self.tab_widget.addTab(self.patcher_widget, "Patcher")
        self.tab_widget.addTab(QWidget(), "Patch Creator")
        self.tab_widget.setTabToolTip(1, "Work in Progress...")
        self.tab_widget.setTabEnabled(1, False)

    def __init_protocol_widget(self) -> None:
        self.protocol_widget = QTextEdit()
        self.protocol_widget.setReadOnly(True)
        self.protocol_widget.setObjectName("protocol")
        self.vlayout.addWidget(self.protocol_widget, 1)

        stdout_handler: StdoutHandler = QApplication.instance().stdout_handler
        stdout_handler.output_signal.connect(self.__handle_stdout)
        stdout_handler.output_signal.emit(stdout_handler._content)

    def __init_progress_bar(self) -> None:
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(4)

        def incr_progress():
            self.progress_bar.setValue(self.progress_bar.value() + 1)

        self.incr_progress_signal.connect(incr_progress)
        self.vlayout.addWidget(self.progress_bar)

    def __init_footer(self) -> None:
        hlayout = QHBoxLayout()
        self.vlayout.addLayout(hlayout)

        self.run_button = QPushButton("Run!")
        self.run_button.setObjectName("accent_button")
        self.run_button.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self.run_button.clicked.connect(self.run)
        self.patcher_widget.valid_signal.connect(self.run_button.setEnabled)
        hlayout.addWidget(self.run_button)

        copy_log_button = QPushButton()
        copy_log_button.setIcon(qta.icon("mdi6.content-copy", color="#ffffff"))
        copy_log_button.setToolTip("Copy Log to Clipboard")
        copy_log_button.clicked.connect(
            lambda: QApplication.clipboard().setText(self.protocol_widget.toPlainText())
        )
        hlayout.addWidget(copy_log_button)

    def __handle_stdout(self, text: str) -> None:
        self.protocol_widget.insertPlainText(text)
        self.protocol_widget.moveCursor(QTextCursor.MoveOperation.End)

    def run(self) -> None:
        self.tab_widget.currentWidget().run()

    def cancel(self) -> None:
        self.tab_widget.currentWidget().cancel()

    def __handle_status_update(self, status_update: StatusUpdate) -> None:
        match status_update:
            case StatusUpdate.Running:
                self.progress_bar.setRange(0, 0)

                self.progress_bar.setProperty("failed", False)

                self.run_button.setText("Cancel")
                self.run_button.setObjectName("")
                self.run_button.clicked.disconnect()
                self.run_button.clicked.connect(self.cancel)

                self.tab_widget.setDisabled(True)

            case StatusUpdate.Successful | StatusUpdate.Ready | StatusUpdate.Failed:
                self.progress_bar.setRange(0, 1)
                self.progress_bar.setValue(1)

                if status_update == StatusUpdate.Failed:
                    self.progress_bar.setProperty("failed", True)

                self.run_button.setText("Run!")
                self.run_button.setObjectName("accent_button")
                self.run_button.clicked.disconnect()
                self.run_button.clicked.connect(self.run)

                self.tab_widget.setDisabled(False)

        self.update()

    def update(self) -> None:
        self.style().unpolish(self)
        self.style().polish(self)

        self.progress_bar.style().unpolish(self.progress_bar)
        self.progress_bar.style().polish(self.progress_bar)

        self.run_button.style().unpolish(self.run_button)
        self.run_button.style().polish(self.run_button)

        super().update()
