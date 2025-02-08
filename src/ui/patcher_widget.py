"""
Copyright (c) Cutleast
"""

import logging
import os
from argparse import Namespace
from pathlib import Path
from typing import Optional

import qtawesome as qta
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.config.config import Config
from core.patcher.patcher import Patcher
from core.utilities.filesystem import is_dir
from core.utilities.status_update import StatusUpdate
from core.utilities.thread import Thread


class PatcherWidget(QWidget):
    """
    Class for patcher widget.
    """

    log: logging.Logger = logging.getLogger("Patcher")

    args: Namespace
    config: Config
    patcher: Patcher
    cwd_path: Path

    patcher_thread: Optional[Thread] = None

    status_signal = Signal(StatusUpdate)
    valid_signal = Signal(bool)

    def __init__(self):
        super().__init__()

        self.args = QApplication.instance().args
        self.config = QApplication.instance().config
        self.patcher = QApplication.instance().patcher
        self.cwd_path = QApplication.instance().cwd_path

        self.__init_ui()

        QApplication.instance().ready_signal.connect(self.__on_app_ready)

        self.status_signal.emit(StatusUpdate.Ready)

    def __on_app_ready(self):
        self.__validate()

        if (patch_path := self.args.patchpath) and (
            original_path := self.args.originalpath
        ):
            self.log.info("Patching automatically...")
            self.patch_path_entry.setCurrentText(patch_path)
            self.mod_path_entry.setCurrentText(original_path)
            self.run()

    def __init_ui(self) -> None:
        self.setObjectName("transparent")

        vlayout = QVBoxLayout()
        self.setLayout(vlayout)

        patch_path_layout = QHBoxLayout()
        vlayout.addLayout(patch_path_layout)
        patch_path_label = QLabel("Path to DIP Patch:")
        patch_path_label.setFixedWidth(175)
        patch_path_layout.addWidget(patch_path_label)
        self.patch_path_entry = QComboBox()
        self.patch_path_entry.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self.patch_path_entry.setEditable(True)
        self.patch_path_entry.currentTextChanged.connect(lambda _: self.__validate())
        patch_path_layout.addWidget(self.patch_path_entry)
        patch_path_button = QPushButton()
        patch_path_button.setIcon(qta.icon("fa.folder-open", color="#ffffff"))

        def browse_patch_path():
            file_dialog = QFileDialog(QApplication.activeModalWidget())
            file_dialog.setWindowTitle("Browse DIP Patch...")
            path = (
                Path(self.patch_path_entry.currentText())
                if self.patch_path_entry.currentText()
                else Path(".")
            )
            path = path.resolve()
            file_dialog.setDirectory(str(path.parent))
            file_dialog.setFileMode(QFileDialog.FileMode.Directory)
            if file_dialog.exec():
                folder = file_dialog.selectedFiles()[0]
                folder = os.path.normpath(folder)
                self.patch_path_entry.setCurrentText(folder)

        patch_path_button.clicked.connect(browse_patch_path)
        patch_path_layout.addWidget(patch_path_button)

        mod_path_layout = QHBoxLayout()
        vlayout.addLayout(mod_path_layout)
        mod_path_label = QLabel("Path to Skyrim's Data folder:")
        mod_path_label.setFixedWidth(175)
        mod_path_layout.addWidget(mod_path_label)
        self.mod_path_entry = QComboBox()
        self.mod_path_entry.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self.mod_path_entry.setEditable(True)
        self.mod_path_entry.currentTextChanged.connect(lambda _: self.__validate())
        mod_path_layout.addWidget(self.mod_path_entry)
        mod_path_button = QPushButton()
        mod_path_button.setIcon(qta.icon("fa.folder-open", color="#ffffff"))

        def browse_mod_path():
            file_dialog = QFileDialog(QApplication.activeModalWidget())
            file_dialog.setWindowTitle("Browse Data folder...")
            path = (
                Path(self.mod_path_entry.currentText())
                if self.mod_path_entry.currentText()
                else Path(".")
            )
            path = path.resolve()
            file_dialog.setDirectory(str(path.parent))
            file_dialog.setFileMode(QFileDialog.FileMode.Directory)
            if file_dialog.exec():
                folder = file_dialog.selectedFiles()[0]
                folder = os.path.normpath(folder)
                self.mod_path_entry.setCurrentText(folder)

        mod_path_button.clicked.connect(browse_mod_path)
        mod_path_layout.addWidget(mod_path_button)

        self.repack_checkbox = QCheckBox(
            "Repack BSA(s) (Warning! The original BSA(s) get(s) overwritten!) (Experimental, use at your own risk!)"
        )
        self.repack_checkbox.setChecked(self.config.repack_bsas)
        self.repack_checkbox.checkStateChanged.connect(self.__on_repack_changed)
        vlayout.addWidget(self.repack_checkbox)

        self.__init_entries()

    def __on_repack_changed(self, check_state: Qt.CheckState) -> None:
        self.config.repack_bsas = self.repack_checkbox.isChecked()

    def __init_entries(self) -> None:
        self.patch_path_entry.addItems(self.patcher.get_patches())

        # If the current working directory is the data folder,
        # set the mod path to the parent folder
        parent_folder = self.cwd_path.parent
        if parent_folder.parts[-1].lower() == "data":
            self.mod_path_entry.setCurrentText(str(parent_folder))
        elif self.cwd_path.parts[-1].lower() == "data":
            self.mod_path_entry.setCurrentText(str(self.cwd_path))

    def __validate(self) -> None:
        patch_path = Path(self.patch_path_entry.currentText()).resolve()
        mod_path = Path(self.mod_path_entry.currentText()).resolve()

        if not self.patcher.check_patch(patch_path):
            self.valid_signal.emit(False)
            return

        if not is_dir(mod_path):
            self.valid_signal.emit(False)
            return

        self.valid_signal.emit(True)

    def run(self) -> None:
        patch_path = Path(self.patch_path_entry.currentText()).resolve()
        mod_path = Path(self.mod_path_entry.currentText()).resolve()

        self.status_signal.emit(StatusUpdate.Running)

        self.patcher_thread = Thread(
            lambda: self.patcher.patch(patch_path, mod_path),
            "PatcherThread",
            self,
        )
        self.patcher_thread.finished.connect(self.on_done)
        self.patcher_thread.start(block=False)

    def on_done(self) -> None:
        # Check if thread was terminated externally
        if self.patcher_thread is None:
            self.status_signal.emit(StatusUpdate.Failed)
            return

        duration: float | Exception = self.patcher_thread.get_result()
        self.patcher_thread = None

        if isinstance(duration, Exception):
            self.log.error(f"Failed to patch: {duration}", exc_info=duration)
            self.status_signal.emit(StatusUpdate.Failed)

            if self.config.silent:
                QApplication.instance().exit(1)
            else:
                message_box = QMessageBox(QApplication.activeModalWidget())
                message_box.setWindowTitle("Patch failed!")
                message_box.setText(f"Failed to patch: {duration}")
                message_box.setStandardButtons(QMessageBox.StandardButton.Ok)
                message_box.exec()

                if self.args.patchpath and self.args.originalpath:
                    QApplication.instance().exit(1)
                else:
                    return

        self.status_signal.emit(StatusUpdate.Successful)

        if self.args.patchpath and self.args.originalpath and not self.config.silent:
            message_box = QMessageBox(QApplication.activeModalWidget())
            message_box.setWindowTitle(f"Patch completed in {duration:.3f} second(s)!")
            message_box.setText("Patch successfully completed.")
            message_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            message_box.exec()
            QApplication.instance().exit()

        elif not self.config.silent:
            message_box = QMessageBox(QApplication.activeModalWidget())
            message_box.setWindowTitle(f"Patch completed in {duration:.3f} second(s)!")
            message_box.setText("Patch successfully completed.")
            message_box.setStandardButtons(
                QMessageBox.StandardButton.No | QMessageBox.StandardButton.Yes
            )
            message_box.setDefaultButton(QMessageBox.StandardButton.Yes)
            message_box.button(QMessageBox.StandardButton.Yes).setText("Close DIP")
            message_box.button(QMessageBox.StandardButton.No).setText("Ok")
            choice = message_box.exec()

            # Handle the user's choice
            if choice == QMessageBox.StandardButton.Yes:
                # Close DIP
                QApplication.instance().exit()

        else:
            QApplication.instance().exit()

    def cancel(self):
        if self.patcher_thread is not None:
            self.patcher_thread.terminate()
            self.patcher_thread = None

        self.mod_path_entry.setEnabled(True)
        self.patch_path_entry.setEnabled(True)
        self.log.warning("Patch incomplete!")
