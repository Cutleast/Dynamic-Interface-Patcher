"""
Copyright (c) Cutleast
"""

import logging
import os
from argparse import Namespace
from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from core.config.config import Config
from core.patcher.patcher import Patcher
from core.utilities.exception_handler import ExceptionHandler
from core.utilities.qt_res_provider import read_resource
from core.utilities.stdout_handler import StdoutHandler
from ui.main_window import MainWindow


class App(QApplication):
    """
    Main application class.
    """

    APP_NAME: str = "Dynamic Interface Patcher"
    APP_VERSION: str = "2.1.0-alpha"

    args: Namespace
    config: Config

    log: logging.Logger = logging.getLogger("App")
    stdout_handler: StdoutHandler
    exception_handler: ExceptionHandler

    patcher: Patcher

    ready_signal = Signal()
    """
    This signal gets emitted when the application is ready.
    """

    def __init__(self, args: Namespace):
        super().__init__()

        self.args = args
        self.config = Config(Path(os.getcwd()) / "config")
        self.patcher = Patcher()

        log_format = "[%(asctime)s.%(msecs)03d]"
        log_format += "[%(levelname)s]"
        log_format += "[%(name)s.%(funcName)s]: "
        log_format += "%(message)s"
        self.log_format = logging.Formatter(log_format, datefmt="%d.%m.%Y %H:%M:%S")
        self.stdout_handler = StdoutHandler(self)
        self.exception_handler = ExceptionHandler(self)
        self.log_str = logging.StreamHandler(self.stdout_handler)
        self.log_str.setFormatter(self.log_format)
        self.log_level = 10  # Debug level
        self.log.setLevel(self.log_level)
        root_log = logging.getLogger()
        root_log.addHandler(self.log_str)
        root_log.setLevel(self.log_level)

        self.apply_args_to_config()

        if self.config.debug_mode:
            self.config.print_settings_to_log()

        self.setApplicationName(self.APP_NAME)
        self.setApplicationDisplayName(self.APP_NAME)
        self.setApplicationVersion(self.APP_VERSION)
        self.setStyleSheet(read_resource(":/style.qss"))
        self.setWindowIcon(QIcon(":/icons/icon.ico"))

        self.log.info(f"Current working directory: {os.getcwd()}")
        self.log.info(f"Executable location: {Path(__file__).resolve().parent}")
        self.log.info("Program started!")

        self.root = MainWindow()

    def apply_args_to_config(self) -> None:
        if self.args.debug:
            self.config.debug_mode = True
            self.log.info("Debug mode enabled.")

        if self.args.silent:
            self.config.silent = True

        if self.args.repack_bsa:
            self.config.repack_bsas = True

        if self.args.output_path:
            self.config.output_folder = Path(self.args.output_path)

    def exec(self) -> int:
        silent: bool = (
            self.args.patchpath and self.args.originalpath
        ) and self.args.silent

        if not silent:
            self.root.show()

        self.ready_signal.emit()

        retcode: int = super().exec()

        self.log.info("Exiting application...")
        self.clean()

        return retcode

    def clean(self) -> None:
        """
        Cleans up temporary application files.
        """

        self.patcher.clean()
