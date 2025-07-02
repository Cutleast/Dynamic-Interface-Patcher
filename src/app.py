"""
Copyright (c) Cutleast
"""

import logging
import os
import sys
from argparse import Namespace
from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from core.config.config import Config
from core.patcher.patcher import Patcher
from core.utilities.exception_handler import ExceptionHandler
from core.utilities.exe_info import get_current_path
from core.utilities.logger import Logger
from core.utilities.qt_res_provider import read_resource
from ui.main_window import MainWindow


class App(QApplication):
    """
    Main application class.
    """

    APP_NAME: str = "Dynamic Interface Patcher"
    APP_VERSION: str = "development"

    args: Namespace
    config: Config

    app_path: Path = get_current_path()
    cwd_path: Path = Path.cwd()

    log: logging.Logger = logging.getLogger("App")
    logger: Logger
    log_path: Path = cwd_path / "DIP.log"
    exception_handler: ExceptionHandler

    main_window: MainWindow
    patcher: Patcher

    ready_signal = Signal()
    """
    This signal gets emitted when the application is ready.
    """

    def __init__(self, args: Namespace):
        super().__init__()

        self.args = args
        self.config = Config.load(self.cwd_path / "config")
        self.config.apply_from_namespace(args)
        self.patcher = Patcher()

        self.logger = Logger(
            self.log_path,
            fmt="[%(asctime)s.%(msecs)03d][%(levelname)s][%(name)s.%(funcName)s]: %(message)s",
            date_fmt="%d.%m.%Y %H:%M:%S",
        )
        self.logger.setLevel(Logger.Level.Debug)

        self.apply_args_to_config()

        if self.config.debug_mode:
            self.config.print_settings_to_log()

        self.setApplicationName(self.APP_NAME)
        self.setApplicationDisplayName(self.APP_NAME)
        self.setApplicationVersion(self.APP_VERSION)
        self.setStyleSheet(read_resource(":/style.qss"))
        self.setWindowIcon(QIcon(":/icons/icon.ico"))

        self.log.info(f"Current working directory: {self.cwd_path}")
        self.log.info(f"Executable location: {self.app_path}")
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
