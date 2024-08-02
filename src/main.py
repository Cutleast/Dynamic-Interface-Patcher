"""
Name: Dynamic Interface Patcher (DIP)
Author: Cutleast
License: Attribution-NonCommercial-NoDerivatives 4.0 International
Python Version: 3.11.2
Qt Version: 6.5.3
"""

import argparse
import logging
import os
import shutil
import sys
import tempfile
import time
import traceback
from pathlib import Path

import pyperclip as clipboard
import qtawesome as qta
import qtpy.QtCore as qtc
import qtpy.QtGui as qtg
import qtpy.QtWidgets as qtw

import errors
import utils


class MainApp(qtw.QApplication):
    """
    Main application class.
    """

    name = "Dynamic Interface Patcher"
    version = "2.0.1"

    incr_progress_signal = qtc.Signal()
    patcher_thread: utils.Thread = None
    done_signal = qtc.Signal()
    start_time: int = None

    cur_path = Path(os.getcwd())

    tmp_dir: Path = None

    def __init__(self):
        super().__init__()

        # Parse commandline arguments
        parser = argparse.ArgumentParser(
            prog=Path(sys.executable).name,
            description=f"{self.name} v{self.version} (c) Cutleast",
        )
        parser.add_argument(
            "-d",
            "--debug",
            help="Enables debug mode so that debug files get outputted.",
            action="store_true",
        )
        parser.add_argument(
            "patchpath",
            nargs="?",
            default="",
            help="Path to patch that gets automatically run. An original mod path must also be given!",
        )
        parser.add_argument(
            "originalpath",
            nargs="?",
            default="",
            help="Path to original mod that gets automatically patched. A patch path must also be given!",
        )
        parser.add_argument(
            "-b",
            "--repack-bsa",
            help="Enables experimental repacking of original BSA file(s).",
            action="store_true",
        )
        parser.add_argument(
            "-o",
            "--output-path",
            help="Specifies output path for patched files."
        )
        self.cmd_args = parser.parse_args()

        self.log = logging.getLogger(self.__repr__())
        log_format = "[%(asctime)s.%(msecs)03d]"
        log_format += "[%(levelname)s]"
        log_format += "[%(name)s.%(funcName)s]: "
        log_format += "%(message)s"
        self.log_format = logging.Formatter(log_format, datefmt="%d.%m.%Y %H:%M:%S")
        self.std_handler = utils.StdoutHandler(self)
        self.log_str = logging.StreamHandler(self.std_handler)
        self.log_str.setFormatter(self.log_format)
        self.log_level = 10  # Debug level
        self.log.setLevel(self.log_level)
        root_log = logging.getLogger()
        root_log.addHandler(self.log_str)
        root_log.setLevel(self.log_level)
        self._excepthook = sys.excepthook
        sys.excepthook = self.handle_exception

        self.root = qtw.QWidget()
        self.root.setObjectName("root")
        self.root.setWindowTitle(f"{self.name} v{self.version}")
        self.root.setStyleSheet((Path(".") / "assets" / "style.qss").read_text())
        self.root.setWindowIcon(qtg.QIcon("./assets/icon.ico"))
        self.root.resize(1000, 500)

        # Fix link color
        palette = self.palette()
        palette.setColor(palette.ColorRole.Link, qtg.QColor("#4994e0"))
        self.setPalette(palette)

        layout = qtw.QVBoxLayout()
        layout.setContentsMargins(0, 15, 0, 0)
        self.root.setLayout(layout)
        self.splitter = qtw.QSplitter()
        self.splitter.setChildrenCollapsible(False)

        self.main_widget = qtw.QWidget()
        self.main_widget.setObjectName("transparent")
        self.splitter.addWidget(self.main_widget)
        self.main_layout = qtw.QVBoxLayout()
        self.main_widget.setLayout(self.main_layout)

        patch_path_layout = qtw.QHBoxLayout()
        patch_path_layout.addSpacing(8)
        layout.addLayout(patch_path_layout)
        patch_path_label = qtw.QLabel("Path to DIP Patch:")
        patch_path_label.setFixedWidth(175)
        patch_path_layout.addWidget(patch_path_label)
        self.patch_path_entry = qtw.QComboBox()
        self.patch_path_entry.setSizePolicy(
            qtw.QSizePolicy.Policy.Expanding, qtw.QSizePolicy.Policy.Preferred
        )
        self.patch_path_entry.setEditable(True)
        patch_path_layout.addWidget(self.patch_path_entry)
        patch_path_button = qtw.QPushButton()
        patch_path_button.setIcon(qta.icon("fa.folder-open", color="#ffffff"))

        def browse_patch_path():
            file_dialog = qtw.QFileDialog(self.root)
            file_dialog.setWindowTitle("Browse DIP Patch...")
            path = (
                Path(self.patch_path_entry.currentText())
                if self.patch_path_entry.currentText()
                else Path(".")
            )
            path = path.resolve()
            file_dialog.setDirectory(str(path.parent))
            file_dialog.setFileMode(qtw.QFileDialog.FileMode.Directory)
            if file_dialog.exec():
                folder = file_dialog.selectedFiles()[0]
                folder = os.path.normpath(folder)
                self.patch_path_entry.setCurrentText(folder)

        patch_path_button.clicked.connect(browse_patch_path)
        patch_path_layout.addWidget(patch_path_button)
        patch_path_layout.addSpacing(8)

        mod_path_layout = qtw.QHBoxLayout()
        self.main_layout.addLayout(mod_path_layout)
        mod_path_label = qtw.QLabel("Path to Skyrim's Data folder:")
        mod_path_label.setFixedWidth(175)
        mod_path_layout.addWidget(mod_path_label)
        self.mod_path_entry = qtw.QComboBox()
        self.mod_path_entry.setSizePolicy(
            qtw.QSizePolicy.Policy.Expanding, qtw.QSizePolicy.Policy.Preferred
        )
        self.mod_path_entry.setEditable(True)
        mod_path_layout.addWidget(self.mod_path_entry)
        mod_path_button = qtw.QPushButton()
        mod_path_button.setIcon(qta.icon("fa.folder-open", color="#ffffff"))

        def browse_mod_path():
            file_dialog = qtw.QFileDialog(self.root)
            file_dialog.setWindowTitle("Browse Data folder...")
            path = (
                Path(self.mod_path_entry.currentText())
                if self.mod_path_entry.currentText()
                else Path(".")
            )
            path = path.resolve()
            file_dialog.setDirectory(str(path.parent))
            file_dialog.setFileMode(qtw.QFileDialog.FileMode.Directory)
            if file_dialog.exec():
                folder = file_dialog.selectedFiles()[0]
                folder = os.path.normpath(folder)
                self.mod_path_entry.setCurrentText(folder)

        mod_path_button.clicked.connect(browse_mod_path)
        mod_path_layout.addWidget(mod_path_button)

        self.repack_checkbox = qtw.QCheckBox(
            "Repack BSA(s) (Warning! The original BSA(s) get(s) overwritten!) (Experimental, use at your own risk!)"
        )
        self.repack_checkbox.setChecked(self.cmd_args.repack_bsa)
        self.main_layout.addWidget(self.repack_checkbox)

        self.protocol_widget = qtw.QTextEdit()
        self.protocol_widget.setReadOnly(True)
        self.protocol_widget.setObjectName("protocol")
        self.main_layout.addWidget(self.protocol_widget, 1)

        self.progress_bar = qtw.QProgressBar()
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(4)

        def incr_progress():
            self.progress_bar.setValue(self.progress_bar.value() + 1)

        self.incr_progress_signal.connect(incr_progress)
        self.main_layout.addWidget(self.progress_bar)

        cmd_layout = qtw.QHBoxLayout()
        self.main_layout.addLayout(cmd_layout)

        self.patch_button = qtw.QPushButton("Patch!")
        self.patch_button.setObjectName("accent_button")
        self.patch_button.setSizePolicy(
            qtw.QSizePolicy.Policy.Expanding, qtw.QSizePolicy.Policy.Preferred
        )
        self.patch_button.clicked.connect(self.run_patcher)
        cmd_layout.addWidget(self.patch_button)

        copy_log_button = qtw.QPushButton()
        copy_log_button.setIcon(qta.icon("mdi6.content-copy", color="#ffffff"))
        copy_log_button.setToolTip("Copy Log to Clipboard")
        copy_log_button.clicked.connect(
            lambda: (clipboard.copy(self.protocol_widget.toPlainText()))
        )
        cmd_layout.addWidget(copy_log_button)

        self.toggle_chain_button = qtw.QPushButton()
        self.toggle_chain_button.setIcon(
            qta.icon("fa.angle-double-left", color="#ffffff")
        )
        self.toggle_chain_button.setToolTip("Toggle Chain Mode")
        self.toggle_chain_button.setDisabled(True)  # WIP
        cmd_layout.addWidget(self.toggle_chain_button)

        docs_label = qtw.QLabel(
            "\
Interested in creating own patches? \
Read the documentation \
<a href='https://github.com/Cutleast/Dynamic-Interface-Patcher/blob/main/DOCUMENTATION.md'>\
here</a>.\
"
        )
        docs_label.setTextFormat(qtc.Qt.TextFormat.RichText)
        docs_label.setAlignment(qtc.Qt.AlignmentFlag.AlignRight)
        docs_label.setOpenExternalLinks(True)
        self.main_layout.addWidget(docs_label)

        # Chain patching list
        self.chain_widget = qtw.QWidget()
        self.chain_widget.setObjectName("transparent")
        self.chain_widget.hide()
        self.splitter.addWidget(self.chain_widget)
        chain_layout = qtw.QVBoxLayout()
        chain_layout.setAlignment(qtc.Qt.AlignmentFlag.AlignTop)
        self.chain_widget.setLayout(chain_layout)

        chain_cmd_layout = qtw.QHBoxLayout()
        chain_layout.addLayout(chain_cmd_layout)
        chain_add_button = qtw.QPushButton("Add Patch to Queue")
        chain_cmd_layout.addWidget(chain_add_button)
        chain_rem_button = qtw.QPushButton("Remove selected Patch")
        chain_rem_button.setEnabled(False)
        chain_cmd_layout.addWidget(chain_rem_button)

        self.chain_list_widget = qtw.QListWidget()
        self.chain_list_widget.setLayoutDirection(qtc.Qt.LayoutDirection.RightToLeft)
        self.chain_list_widget.setDragDropMode(
            qtw.QListWidget.DragDropMode.InternalMove
        )
        self.chain_list_widget.setDragEnabled(True)
        chain_layout.addWidget(self.chain_list_widget, 1)
        self.chain_list_widget.itemSelectionChanged.connect(
            lambda: chain_rem_button.setEnabled(True)
        )

        def add_chain_patch():
            path = self.patch_path_entry.currentText().strip()
            if not path:
                return
            queue_items = utils.get_list_widget_items(self.chain_list_widget)
            path_items = utils.get_combobox_items(self.patch_path_entry)
            if path not in queue_items:
                self.chain_list_widget.addItem(path)
                if path in path_items:
                    self.patch_path_entry.removeItem(path_items.index(path))
                self.patch_path_entry.setCurrentIndex(0)

        def rem_chain_patch():
            current_patch = self.chain_list_widget.takeItem(
                self.chain_list_widget.currentRow()
            ).text()
            self.patch_path_entry.addItem(current_patch)
            if not self.chain_list_widget.count():
                chain_rem_button.setDisabled(True)

        chain_add_button.clicked.connect(add_chain_patch)
        chain_rem_button.clicked.connect(rem_chain_patch)

        drag_hint_label = qtw.QLabel("Rearrange Patches by Dragging")
        chain_layout.addWidget(drag_hint_label)

        # Toggle chain patch logic
        def toggle_chain_mode():
            if self.chain_widget.isVisible():
                self.chain_widget.hide()
                self.toggle_chain_button.setIcon(
                    qta.icon("fa.angle-double-left", color="#ffffff")
                )
                self.log.info("Chain Mode disabled.")
                self.patch_button.setText("Patch!")
            else:
                self.chain_widget.show()
                self.toggle_chain_button.setIcon(
                    qta.icon("fa.angle-double-right", color="#ffffff")
                )
                self.log.info("Chain Mode enabled.")
                self.patch_button.setText("Chain Patch!")

        self.toggle_chain_button.clicked.connect(toggle_chain_mode)

        layout.addWidget(self.splitter)

        self.std_handler.output_signal.connect(self.handle_stdout)
        self.std_handler.output_signal.emit(self.std_handler._content)
        self.done_signal.connect(self.done)

        self.log.debug("Scanning for patches...")
        self.patch_path_entry.addItems(self.get_patches())

        # If the current working directory is the data folder,
        # set the mod path to the parent folder
        parent_folder = Path(os.getcwd()).parent
        if parent_folder.parts[-1].lower() == "data":
            self.mod_path_entry.setCurrentText(str(parent_folder))

        self.log.info(f"Current working directory: {os.getcwd()}")
        self.log.info(f"Executable location: {Path(__file__).resolve().parent}")

        self.log.debug("Program started!")

        self.root.show()
        utils.apply_dark_title_bar(self.root)

        if (patch_path := self.cmd_args.patchpath) and (
            original_path := self.cmd_args.originalpath
        ):
            self.log.info("Patching automatically...")
            self.patch_path_entry.setCurrentText(patch_path)
            self.mod_path_entry.setCurrentText(original_path)
            self.run_patcher()

        if self.cmd_args.debug:
            self.debug = True
            self.log.info("Debug mode enabled.")
        else:
            self.debug = False

    def __repr__(self):
        return "MainApp"

    def handle_exception(self, exc_type, exc_value, exc_traceback):
        tb = "".join(
            traceback.format_exception(exc_type, value=exc_value, tb=exc_traceback)
        )
        # Remove dev environment paths from traceback
        # cx_freeze, why ever, keeps them when building
        tb = tb.replace(
            "C:\\Users\\robin\\OneDrive\\Modding\\Mods\\Dynamic-Interface-Patcher\\src\\",
            "",
        )

        self.log.critical("An uncaught exception occured:\n" + tb)

    def handle_stdout(self, text):
        self.protocol_widget.insertPlainText(text)
        self.protocol_widget.moveCursor(qtg.QTextCursor.MoveOperation.End)

    def get_patches(self):
        parent_folder = Path(os.getcwd()).parent

        self.log.debug(f"Searching in '{parent_folder}'...")

        paths: list[str] = []

        for folder in parent_folder.glob(".\\*DIP*\\Patch"):
            paths.append(str(folder.parent))

        return paths

    def run_patcher(self):
        if self.chain_widget.isHidden():
            try:
                self.patcher = patcher.Patcher(
                    self,
                    Path(self.patch_path_entry.currentText()),
                    Path(self.mod_path_entry.currentText()),
                )
                self.patcher_thread = utils.Thread(
                    lambda: self.patcher.patch(
                        repack_bsas=self.repack_checkbox.isChecked()
                    ),
                    "PatcherThread",
                    self,
                )
                self.progress_bar.setRange(0, 0)
            except errors.InvalidPatchError as ex:
                self.log.error(f"Selected patch is invalid: {ex}")
                return
        elif self.chain_list_widget.count():
            self.progress_bar.setRange(0, self.chain_list_widget.count())
            self.patcher_thread = utils.Thread(
                self.run_chain_patch, "PatcherThread", self
            )
        else:
            return

        self.patch_button.setText("Cancel")
        self.patch_button.clicked.disconnect(self.run_patcher)
        self.patch_button.clicked.connect(self.cancel_patcher)
        self.mod_path_entry.setDisabled(True)
        self.patch_path_entry.setDisabled(True)
        self.chain_widget.setDisabled(True)
        self.toggle_chain_button.setDisabled(True)
        self.start_time = time.time()
        self.patcher_thread.start()

    def run_chain_patch(self):
        patch_path = Path(self.chain_list_widget.item(0).text())
        mod_path = Path(self.mod_path_entry.currentText())
        self.patcher = patcher.Patcher(
            app=self, patch_path=patch_path, original_mod_path=mod_path
        )
        self.patcher.patch()
        self.incr_progress_signal.emit()
        for i in range(self.chain_list_widget.count()):
            patch_path = Path(self.chain_list_widget.item(0).text())
            mod_path = Path(self.mod_path_entry.currentText())
            self.patcher = patcher.Patcher(
                app=self, patch_path=patch_path, original_mod_path=mod_path
            )
            self.patcher.patch(True)
            self.incr_progress_signal.emit()
        self.done_signal.emit()

    def done(self):
        self.mod_path_entry.setEnabled(True)
        self.patch_path_entry.setEnabled(True)
        self.chain_widget.setEnabled(True)
        # self.toggle_chain_button.setEnabled(True)  # WIP
        self.patch_button.setText("Patch!")
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(1)
        self.patch_button.clicked.disconnect(self.cancel_patcher)
        self.patch_button.clicked.connect(self.run_patcher)

        self.log.info(
            f"Patching done in {(time.time() - self.start_time):.3f} second(s)."
        )

        if self.cmd_args.patchpath and self.cmd_args.originalpath:
            self.exit()

        message_box = qtw.QMessageBox(self.root)
        message_box.setWindowIcon(self.root.windowIcon())
        message_box.setStyleSheet(self.root.styleSheet())
        utils.apply_dark_title_bar(message_box)
        message_box.setWindowTitle(
            f"Patch completed in {(time.time() - self.start_time):.3f} second(s)"
        )
        message_box.setText("Patch successfully completed")
        message_box.setStandardButtons(
            qtw.QMessageBox.StandardButton.No | qtw.QMessageBox.StandardButton.Yes
        )
        message_box.setDefaultButton(qtw.QMessageBox.StandardButton.Yes)
        message_box.button(qtw.QMessageBox.StandardButton.Yes).setText("Close DIP")
        message_box.button(qtw.QMessageBox.StandardButton.No).setText("Ok")
        choice = message_box.exec()

        # Handle the user's choice
        if choice == qtw.QMessageBox.StandardButton.Yes:
            # Close DIP
            self.exit()

    def cancel_patcher(self):
        self.patcher_thread.terminate()

        if self.patcher.ffdec_interface is not None:
            if self.patcher.ffdec_interface.pid is not None:
                utils.kill_child_process(self.patcher.ffdec_interface.pid)
                self.log.info(
                    f"Killed FFDec with pid {self.patcher.ffdec_interface.pid}."
                )
                self.patcher.ffdec_interface.pid = None

        if self.tmp_dir is not None:
            if self.tmp_dir.is_dir():
                shutil.rmtree(self.tmp_dir)
                self.tmp_dir = None
                self.log.info("Cleaned up temporary folder.")

        self.mod_path_entry.setEnabled(True)
        self.patch_path_entry.setEnabled(True)
        self.chain_widget.setEnabled(True)
        self.toggle_chain_button.setEnabled(True)
        self.patch_button.setText("Patch!")
        self.patch_button.clicked.disconnect(self.cancel_patcher)
        self.patch_button.clicked.connect(self.run_patcher)
        self.progress_bar.setRange(0, 1)
        self.log.warning("Patch incomplete!")

    def get_tmp_dir(self):
        if self.tmp_dir is None:
            self.tmp_dir = Path(tempfile.mkdtemp(prefix="DIP_"))
            self.log.debug(f"Created temporary directory at {str(self.tmp_dir)!r}.")

        return self.tmp_dir

    def setup(self):
        """
        Downloads Java Runtime, extracts it and redirects FFDec to it.
        """

        jre_path = self.cur_path / "assets" / "jre_binaries" / "jre.7z"

        tmp_folder = self.get_tmp_dir()

        utils.extract_archive(jre_path, tmp_folder)

        java_paths = list(tmp_folder.glob("*/bin/java.exe"))

        if not java_paths:
            raise Exception("Archive does not contain a valid java.exe!")

        java_path = java_paths[0]

        # Write jre_path in ffdec.bat
        ffdec_bat_path = self.cur_path / "assets" / "ffdec" / "ffdec.bat"
        orig_bat_path = ffdec_bat_path.with_stem("ffdec_orig")

        text = orig_bat_path.read_text()
        lines = text.splitlines()
        last_line = lines[-1]

        last_line = last_line.replace("java", f'"{java_path}"', 1)
        lines[-1] = last_line

        ffdec_bat_path.write_text("\n".join(lines))

    def exec(self):
        super().exec()

        if self.tmp_dir:
            shutil.rmtree(self.tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    import patcher

    app = MainApp()
    app.exec()
