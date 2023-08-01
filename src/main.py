"""
Name: Dynamic Interface Patcher (DIP)
Author: Cutleast
License: Attribution-NonCommercial-NoDerivatives 4.0 International
Python Version: 3.11.2
Qt Version: 6.5.1
"""

import argparse
import logging
import os
import shutil
import pyperclip as clipboard
import sys
import time
from pathlib import Path

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
    version = "1.0.1"

    patcher_thread: utils.Thread = None
    done_signal = qtc.Signal()
    start_time: int = None

    def __init__(self):
        super().__init__()

        # Parse commandline arguments
        parser = argparse.ArgumentParser(
            prog=Path(sys.executable).name,
            description=f"{self.name} v{self.version} (c) Cutleast"
        )
        parser.add_argument("-d", "--debug", help="Enables debug mode so that debug files get outputted.", action='store_true')
        parser.add_argument("patchpath", nargs='?', default='', help="Path to patch that gets automatically run. An original mod path must also be given!")
        parser.add_argument("originalpath", nargs='?', default='', help="Path to original mod that gets automatically patched. A patch path must also be given!")
        self.cmd_args = parser.parse_args()

        self.log = logging.getLogger(self.__repr__())
        log_format = "[%(asctime)s.%(msecs)03d]"
        log_format += "[%(levelname)s]"
        log_format += "[%(name)s.%(funcName)s]: "
        log_format += "%(message)s"
        self.log_format = logging.Formatter(
            log_format,
            datefmt="%d.%m.%Y %H:%M:%S"
        )
        self.std_handler = utils.StdoutHandler(self)
        self.log_str = logging.StreamHandler(self.std_handler)
        self.log_str.setFormatter(self.log_format)
        self.log.addHandler(self.log_str)
        self.log_level = 10 # Debug level
        self.log.setLevel(self.log_level)
        self._excepthook = sys.excepthook
        sys.excepthook = self.handle_exception

        self.root = qtw.QWidget()
        self.root.setWindowTitle(f"{self.name} v{self.version}")
        self.root.setStyleSheet((Path(".") / "assets" / "style.qss").read_text())
        self.root.setWindowIcon(qtg.QIcon("./assets/icon.ico"))
        self.root.setMinimumWidth(1000)
        self.root.setMinimumHeight(500)

        self.layout = qtw.QVBoxLayout()
        self.root.setLayout(self.layout)

        self.conf_layout = qtw.QGridLayout()
        self.conf_layout.setColumnStretch(1, 1)
        self.layout.addLayout(self.conf_layout)

        patch_path_label = qtw.QLabel("Enter Path to DIP Patch:")
        self.conf_layout.addWidget(patch_path_label, 0, 0)
        self.patch_path_entry = qtw.QComboBox()
        self.patch_path_entry.setEditable(True)
        self.conf_layout.addWidget(self.patch_path_entry, 0, 1)
        patch_path_button = qtw.QPushButton("Browse...")

        def browse_patch_path():
            file_dialog = qtw.QFileDialog(self.root)
            file_dialog.setWindowTitle("Browse DIP Patch...")
            path = Path(self.patch_path_entry.currentText()) if self.patch_path_entry.currentText() else Path(".")
            path = path.resolve()
            file_dialog.setDirectory(str(path.parent))
            file_dialog.setFileMode(qtw.QFileDialog.FileMode.Directory)
            if file_dialog.exec():
                folder = file_dialog.selectedFiles()[0]
                folder = os.path.normpath(folder)
                self.patch_path_entry.setCurrentText(folder)
        patch_path_button.clicked.connect(browse_patch_path)
        self.conf_layout.addWidget(patch_path_button, 0, 2)

        mod_path_label = qtw.QLabel("Enter Path to patched Mod:")
        self.conf_layout.addWidget(mod_path_label, 1, 0)
        self.mod_path_entry = qtw.QComboBox()
        self.mod_path_entry.setEditable(True)
        self.conf_layout.addWidget(self.mod_path_entry, 1, 1)
        mod_path_button = qtw.QPushButton("Browse...")

        def browse_mod_path():
            file_dialog = qtw.QFileDialog(self.root)
            file_dialog.setWindowTitle("Browse patched Mod...")
            path = Path(self.mod_path_entry.currentText()) if self.mod_path_entry.currentText() else Path(".")
            path = path.resolve()
            file_dialog.setDirectory(str(path.parent))
            file_dialog.setFileMode(qtw.QFileDialog.FileMode.Directory)
            if file_dialog.exec():
                folder = file_dialog.selectedFiles()[0]
                folder = os.path.normpath(folder)
                self.mod_path_entry.setCurrentText(folder)
        mod_path_button.clicked.connect(browse_mod_path)
        self.conf_layout.addWidget(mod_path_button, 1, 2)

        self.protocol_widget = qtw.QTextEdit()
        self.protocol_widget.setReadOnly(True)
        self.protocol_widget.setObjectName("protocol")
        self.layout.addWidget(self.protocol_widget, 1)

        cmd_layout = qtw.QHBoxLayout()
        self.layout.addLayout(cmd_layout)

        self.patch_button = qtw.QPushButton("Patch!")
        self.patch_button.clicked.connect(self.run_patcher)
        cmd_layout.addWidget(self.patch_button)

        copy_log_button = qtw.QPushButton("Copy Log")
        copy_log_button.setFixedWidth(120)
        copy_log_button.clicked.connect(lambda: (
            clipboard.copy(self.protocol_widget.toPlainText())
        ))
        cmd_layout.addWidget(copy_log_button)

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
        self.layout.addWidget(docs_label)

        # Fix link color
        palette = self.palette()
        palette.setColor(
            palette.ColorRole.Link,
            qtg.QColor("#006fde")
        )
        self.setPalette(palette)

        self.std_handler.output_signal.connect(self.handle_stdout)
        self.std_handler.output_signal.emit(self.std_handler._content)
        self.done_signal.connect(self.done)

        self.log.debug("Scanning for patches...")
        self.patch_path_entry.addItems(self.get_patches())
        
        self.log.info(f"Current working directory: {os.getcwd()}")
        self.log.info(f"Executable location: {Path(__file__).resolve().parent}")

        self.check_java()

        self.log.debug("Program started!")

        self.root.show()
        utils.apply_dark_title_bar(self.root)

        if (patch_path := self.cmd_args.patchpath) and (original_path := self.cmd_args.originalpath):
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

    def check_java(self):
        self.log.info("Checking for java installation...")

        java_installed = utils.check_java()

        if not java_installed:
            self.log.critical("Java could not be found! Patching not possible!")
            message_box = qtw.QMessageBox(self.root)
            message_box.setWindowIcon(self.root.windowIcon())
            message_box.setStyleSheet(self.root.styleSheet())
            utils.apply_dark_title_bar(message_box)
            message_box.setWindowTitle("No Java installed!")
            message_box.setText(
                "Java could not be found on PATH.\nMake sure that Java 64-bit is installed and try again!"
            )
            message_box.setStandardButtons(
                qtw.QMessageBox.StandardButton.No
                | qtw.QMessageBox.StandardButton.Yes
            )
            message_box.setDefaultButton(
                qtw.QMessageBox.StandardButton.Yes
            )
            message_box.button(
                qtw.QMessageBox.StandardButton.Yes
            ).setText("Open Java Website")
            message_box.button(
                qtw.QMessageBox.StandardButton.No
            ).setText("Exit")
            choice = message_box.exec()

            # Handle the user's choice
            if choice == qtw.QMessageBox.StandardButton.Yes:
                # Open nexus mods file page
                os.startfile(
                    "https://www.java.com/en/download/"
                )

            self.exit()

        self.log.info("Java found.")

    def handle_exception(self, exc_type, exc_value, exc_traceback):
        self.log.critical(
            "An uncaught exception occured:",
            exc_info=(exc_type, exc_value, exc_traceback)
        )

    def handle_stdout(self, text):
        self.protocol_widget.insertPlainText(text)
        self.protocol_widget.moveCursor(qtg.QTextCursor.MoveOperation.End)

    def get_patches(self):
        parent_folder = Path(os.getcwd()).resolve().parent

        self.log.debug(f"Searching in '{parent_folder}'...")

        paths: list[str] = []

        for folder in parent_folder.glob("*\\*DIP*\\Patch"):
            paths.append(str(folder.resolve().parent))

        return paths

    def run_patcher(self):
        try:
            self.patcher = patcher.Patcher(
                self,
                Path(self.patch_path_entry.currentText()).resolve(),
                Path(self.mod_path_entry.currentText()).resolve()
            )
            self.patcher_thread = utils.Thread(
                self.patcher.patch,
                "PatcherThread",
                self
            )
        except errors.InvalidPatchError as ex:
            self.log.error(f"Selected patch is invalid: {ex}")
            return

        self.patch_button.setText("Cancel")
        self.patch_button.clicked.disconnect(self.run_patcher)
        self.patch_button.clicked.connect(self.cancel_patcher)

        self.start_time = time.time()

        self.patcher_thread.start()

    def done(self):
        self.patch_button.setText("Patch!")
        self.patch_button.clicked.disconnect(self.cancel_patcher)
        self.patch_button.clicked.connect(self.run_patcher)

        self.log.info(f"Patching done in {(time.time() - self.start_time):.3f} second(s).")

        if self.cmd_args.patchpath and self.cmd_args.originalpath:
            self.exit()

        message_box = qtw.QMessageBox(self.root)
        message_box.setWindowIcon(self.root.windowIcon())
        message_box.setStyleSheet(self.root.styleSheet())
        utils.apply_dark_title_bar(message_box)
        message_box.setWindowTitle(f"Patch completed in {(time.time() - self.start_time):.3f} second(s)")
        message_box.setText(
            "Patch successfully completed"
        )
        message_box.setStandardButtons(
            qtw.QMessageBox.StandardButton.No
            | qtw.QMessageBox.StandardButton.Yes
        )
        message_box.setDefaultButton(
            qtw.QMessageBox.StandardButton.Yes
        )
        message_box.button(
            qtw.QMessageBox.StandardButton.Yes
        ).setText("Close DIP")
        message_box.button(
            qtw.QMessageBox.StandardButton.No
        ).setText("Ok")
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
                self.log.info(f"Killed FFDec with pid {self.patcher.ffdec_interface.pid}.")
                self.patcher.ffdec_interface.pid = None

        if self.patcher.tmpdir is not None:
            if self.patcher.tmpdir.is_dir():
                shutil.rmtree(self.patcher.tmpdir)
                self.log.info("Cleaned up temporary folder.")

        self.patch_button.setText("Patch!")
        self.patch_button.clicked.disconnect(self.cancel_patcher)
        self.patch_button.clicked.connect(self.run_patcher)
        self.log.warning("Patch incomplete!")


if __name__ == "__main__":
    import patcher

    app = MainApp()
    app.exec()
