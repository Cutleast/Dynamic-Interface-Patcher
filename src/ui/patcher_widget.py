"""
Copyright (c) Cutleast
"""

import logging
import os
from pathlib import Path
from typing import override

from cutleast_core_lib.core.utilities.thread import Thread
from cutleast_core_lib.ui.utilities.icon_provider import IconProvider
from PySide6.QtCore import Qt
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
)

from core.config.config import Config
from core.patch.patch_provider import PatchProvider
from core.patcher.patcher import Patcher
from core.utilities.filesystem import is_dir
from core.utilities.status_update import StatusUpdate

from .base_tab import BaseTab


class PatcherWidget(BaseTab):
    """
    Class for patcher widget.
    """

    log: logging.Logger = logging.getLogger("Patcher")

    config: Config
    patcher: Patcher
    cwd_path: Path = Path.cwd()

    __patch_path_entry: QComboBox
    __mod_path_entry: QComboBox
    __repack_checkbox: QCheckBox

    def __init__(self, config: Config, patcher: Patcher) -> None:
        super().__init__()

        self.config = config
        self.patcher = patcher

        self.__init_ui()

        self.status_signal.emit(StatusUpdate.Ready)

    def __init_ui(self) -> None:
        vlayout = QVBoxLayout()
        self.setLayout(vlayout)

        patch_path_layout = QHBoxLayout()
        vlayout.addLayout(patch_path_layout)
        patch_path_label = QLabel("Path to DIP Patch:")
        patch_path_label.setFixedWidth(175)
        patch_path_layout.addWidget(patch_path_label)
        self.__patch_path_entry = QComboBox()
        self.__patch_path_entry.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self.__patch_path_entry.setEditable(True)
        self.__patch_path_entry.currentTextChanged.connect(lambda _: self.__validate())
        patch_path_layout.addWidget(self.__patch_path_entry)
        patch_path_button = QPushButton()
        patch_path_button.setIcon(IconProvider.get_qta_icon("fa5s.folder-open"))

        def browse_patch_path():
            file_dialog = QFileDialog(QApplication.activeModalWidget())
            file_dialog.setWindowTitle("Browse DIP Patch...")
            path = (
                Path(self.__patch_path_entry.currentText())
                if self.__patch_path_entry.currentText()
                else Path(".")
            )
            path = path.resolve()
            file_dialog.setDirectory(str(path.parent))
            file_dialog.setFileMode(QFileDialog.FileMode.Directory)
            if file_dialog.exec():
                folder = file_dialog.selectedFiles()[0]
                folder = os.path.normpath(folder)
                self.__patch_path_entry.setCurrentText(folder)

        patch_path_button.clicked.connect(browse_patch_path)
        patch_path_layout.addWidget(patch_path_button)

        mod_path_layout = QHBoxLayout()
        vlayout.addLayout(mod_path_layout)
        mod_path_label = QLabel("Path to Skyrim's Data folder:")
        mod_path_label.setFixedWidth(175)
        mod_path_layout.addWidget(mod_path_label)
        self.__mod_path_entry = QComboBox()
        self.__mod_path_entry.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self.__mod_path_entry.setEditable(True)
        self.__mod_path_entry.currentTextChanged.connect(lambda _: self.__validate())
        mod_path_layout.addWidget(self.__mod_path_entry)
        mod_path_button = QPushButton()
        mod_path_button.setIcon(IconProvider.get_qta_icon("fa5s.folder-open"))

        def browse_mod_path():
            file_dialog = QFileDialog(QApplication.activeModalWidget())
            file_dialog.setWindowTitle("Browse Data folder...")
            path = (
                Path(self.__mod_path_entry.currentText())
                if self.__mod_path_entry.currentText()
                else Path(".")
            )
            path = path.resolve()
            file_dialog.setDirectory(str(path.parent))
            file_dialog.setFileMode(QFileDialog.FileMode.Directory)
            if file_dialog.exec():
                folder = file_dialog.selectedFiles()[0]
                folder = os.path.normpath(folder)
                self.__mod_path_entry.setCurrentText(folder)

        mod_path_button.clicked.connect(browse_mod_path)
        mod_path_layout.addWidget(mod_path_button)

        self.__repack_checkbox = QCheckBox(
            "Repack BSA(s) (Warning! The original BSA(s) get(s) overwritten!) (Experimental, use at your own risk!)"
        )
        self.__repack_checkbox.setChecked(self.config.repack_bsas)
        self.__repack_checkbox.checkStateChanged.connect(self.__on_repack_changed)
        vlayout.addWidget(self.__repack_checkbox)

        self.__init_entries()

    def __on_repack_changed(self, check_state: Qt.CheckState) -> None:
        self.config.repack_bsas = self.__repack_checkbox.isChecked()

    def __init_entries(self) -> None:
        self.__patch_path_entry.addItems(PatchProvider.get_patches())

        # If the current working directory is the data folder,
        # set the mod path to the parent folder
        parent_folder = self.cwd_path.parent
        if parent_folder.parts[-1].lower() == "data":
            self.__mod_path_entry.setCurrentText(str(parent_folder))
        elif self.cwd_path.parts[-1].lower() == "data":
            self.__mod_path_entry.setCurrentText(str(self.cwd_path))

        if self.config.patch_path is not None:
            self.__patch_path_entry.setCurrentText(str(self.config.patch_path))

        if self.config.original_path is not None:
            self.__mod_path_entry.setCurrentText(str(self.config.original_path))

    def __validate(self) -> None:
        patch_path = Path(self.__patch_path_entry.currentText()).resolve()
        mod_path = Path(self.__mod_path_entry.currentText()).resolve()

        if not PatchProvider.check_patch(patch_path):
            self.valid_signal.emit(False)
            return

        if not is_dir(mod_path):
            self.valid_signal.emit(False)
            return

        self.valid_signal.emit(True)

    @override
    def run(self) -> None:
        patch_path = Path(self.__patch_path_entry.currentText()).resolve()
        mod_path = Path(self.__mod_path_entry.currentText()).resolve()

        self.status_signal.emit(StatusUpdate.Running)

        self._thread = Thread(
            lambda: self.patcher.patch(patch_path, mod_path), "PatcherThread", self
        )
        self._thread.finished.connect(self.on_done)
        self._thread.start()

    def on_done(self) -> None:
        # Check if thread was terminated externally
        if self._thread is None:
            self.status_signal.emit(StatusUpdate.Failed)
            return

        duration: float | Exception = self._thread.get_result()
        self._thread = None

        if isinstance(duration, Exception):
            self.log.error(f"Failed to patch: {duration}", exc_info=duration)
            self.status_signal.emit(StatusUpdate.Failed)

            if self.config.silent:
                QApplication.exit(1)
            else:
                message_box = QMessageBox(QApplication.activeModalWidget())
                message_box.setWindowTitle("Patch failed!")
                message_box.setText(f"Failed to patch: {duration}")
                message_box.setStandardButtons(QMessageBox.StandardButton.Ok)
                message_box.exec()

                if self.config.auto_patch:
                    QApplication.exit(1)

            return

        self.status_signal.emit(StatusUpdate.Successful)

        if self.config.auto_patch and not self.config.silent:
            message_box = QMessageBox(QApplication.activeModalWidget())
            message_box.setWindowTitle(f"Patch completed in {duration:.3f} second(s)!")
            message_box.setText("Patch successfully completed.")
            message_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            message_box.exec()
            QApplication.exit()

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
                QApplication.exit()

        else:
            QApplication.exit()

    @override
    def cancel(self) -> None:
        if self._thread is not None:
            self._thread.terminate()
            self._thread = None

        self.__mod_path_entry.setEnabled(True)
        self.__patch_path_entry.setEnabled(True)
        self.log.warning("Patch incomplete!")
