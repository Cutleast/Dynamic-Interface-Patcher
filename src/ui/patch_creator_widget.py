"""
Copyright (c) Cutleast
"""

import logging
from pathlib import Path
from typing import Optional, override

from PySide6.QtWidgets import QApplication, QFileDialog, QFormLayout, QMessageBox

from core.config.config import Config
from core.config.patch_creator_config import PatchCreatorConfig
from core.patch_creator.patch_creator import PatchCreator
from core.utilities.status_update import StatusUpdate
from core.utilities.thread import Thread

from .base_tab import BaseTab
from .widgets.browse_edit import BrowseLineEdit


class PatchCreatorWidget(BaseTab):
    """
    Class for patch creator widget.
    """

    log: logging.Logger = logging.getLogger("PatchCreator")

    config: Config
    patch_creator_config: PatchCreatorConfig
    patch_creator: PatchCreator
    cwd_path: Path = Path.cwd()

    __original_path_entry: BrowseLineEdit
    __patched_path_entry: BrowseLineEdit
    __output_path_entry: BrowseLineEdit

    def __init__(
        self,
        config: Config,
        patch_creator_config: PatchCreatorConfig,
        patch_creator: PatchCreator,
    ) -> None:
        """
        Args:
            config (Config): General app configuration.
            patch_creator_config (PatchCreatorConfig): Patch creator configuration.
            patch_creator (PatchCreator): Patch creator.
        """

        super().__init__()

        self.config = config
        self.patch_creator_config = patch_creator_config
        self.patch_creator = patch_creator

        self.__init_ui()

        self.__original_path_entry.pathChanged.connect(lambda _, __: self.__on_change())
        self.__patched_path_entry.pathChanged.connect(lambda _, __: self.__on_change())
        self.__output_path_entry.pathChanged.connect(lambda _, __: self.__on_change())

        self.status_signal.emit(StatusUpdate.Ready)

    def __init_ui(self) -> None:
        flayout = QFormLayout()
        self.setLayout(flayout)

        self.__original_path_entry = BrowseLineEdit(
            self.config.original_path, self.cwd_path
        )
        self.__original_path_entry.setFileMode(QFileDialog.FileMode.Directory)
        flayout.addRow("Path to original mod:", self.__original_path_entry)

        self.__patched_path_entry = BrowseLineEdit(
            self.config.patch_path, self.cwd_path
        )
        self.__patched_path_entry.setFileMode(QFileDialog.FileMode.Directory)
        flayout.addRow("Path to patched mod:", self.__patched_path_entry)

        self.__output_path_entry = BrowseLineEdit(
            self.config.output_folder, self.cwd_path
        )
        self.__output_path_entry.setFileMode(QFileDialog.FileMode.Directory)
        flayout.addRow("Path to output folder:", self.__output_path_entry)

    def __on_change(self) -> None:
        original_path: Optional[Path] = self.__original_path_entry.getPath(
            absolute=True
        )
        patched_path: Optional[Path] = self.__patched_path_entry.getPath(absolute=True)
        output_path: Optional[Path] = self.__output_path_entry.getPath(absolute=True)

        self.config.output_folder = output_path

        self.valid_signal.emit(
            original_path is not None
            and original_path.is_dir()
            and patched_path is not None
            and patched_path.is_dir()
        )

    def __set_input_enabled(self, enabled: bool) -> None:
        self.__original_path_entry.setEnabled(enabled)
        self.__patched_path_entry.setEnabled(enabled)
        self.__output_path_entry.setEnabled(enabled)

    @override
    def run(self) -> None:
        original_path: Optional[Path] = self.__original_path_entry.getPath(
            absolute=True
        )
        patched_path: Optional[Path] = self.__patched_path_entry.getPath(absolute=True)

        if original_path is None or patched_path is None:
            self.status_signal.emit(StatusUpdate.Failed)
            self.log.error("Missing input path!")
            return

        self.status_signal.emit(StatusUpdate.Running)

        self._thread = Thread(
            lambda: self.patch_creator.create_patch(patched_path, original_path),
            "PatchCreatorThread",
            self,
        )
        self._thread.finished.connect(self.__on_done)
        self._thread.start()

    def __on_done(self) -> None:
        # Check if thread was terminated externally
        if self._thread is None:
            self.status_signal.emit(StatusUpdate.Failed)
            return

        duration: float | Exception = self._thread.get_result()
        self._thread = None

        if isinstance(duration, Exception):
            self.log.error(f"Failed to create patch: {duration}", exc_info=duration)
            self.status_signal.emit(StatusUpdate.Failed)

            message_box = QMessageBox(QApplication.activeModalWidget())
            message_box.setWindowTitle("Patch creation failed!")
            message_box.setText(f"Failed to create patch: {duration}")
            message_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            message_box.exec()
            return

        self.status_signal.emit(StatusUpdate.Successful)

        message_box = QMessageBox(QApplication.activeModalWidget())
        message_box.setWindowTitle(f"Patch created in {duration:.3f} second(s)!")
        message_box.setText("Patch successfully created.")
        message_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        message_box.exec()

    @override
    def cancel(self) -> None:
        if self._thread is not None:
            self._thread.terminate()
            self._thread = None

        self.__set_input_enabled(True)
        self.log.warning("Patch creation incomplete!")
