"""
Copyright (c) Cutleast
"""

import logging
import platform
import subprocess
import sys
from argparse import Namespace
from pathlib import Path
from typing import override

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from core.config.config import Config
from core.config.patch_creator_config import PatchCreatorConfig
from core.patch_creator.patch_creator import PatchCreator
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
    patch_creator_config: PatchCreatorConfig

    app_path: Path = get_current_path()
    cwd_path: Path = Path.cwd()

    log: logging.Logger = logging.getLogger("App")
    logger: Logger
    log_path: Path = cwd_path / "DIP.log"
    exception_handler: ExceptionHandler

    main_window: MainWindow
    patcher: Patcher
    patch_creator: PatchCreator

    def __init__(self, args: Namespace) -> None:
        super().__init__()

        self.args = args
        self.config = Config.load(self.app_path / "config")
        self.config.apply_from_namespace(args)
        self.patch_creator_config = PatchCreatorConfig.load(self.app_path / "config")

        self.logger = Logger(
            self.log_path,
            fmt="[%(asctime)s.%(msecs)03d][%(levelname)s][%(name)s.%(funcName)s]: %(message)s",
            date_fmt="%d.%m.%Y %H:%M:%S",
        )
        self.logger.setLevel(Logger.Level.Debug)

        self.setApplicationName(App.APP_NAME)
        self.setApplicationDisplayName(App.APP_NAME)
        self.setApplicationVersion(App.APP_VERSION)
        self.setStyleSheet(read_resource(":/style.qss"))
        self.setWindowIcon(QIcon(":/icons/icon.ico"))

        self.log_basic_info()
        self.config.print_settings_to_log()
        self.log.info("App started!")

        self.exception_handler = ExceptionHandler(self)
        self.patcher = Patcher(self.config)
        self.patch_creator = PatchCreator(self.config, self.patch_creator_config)
        self.main_window = MainWindow(
            self.logger,
            self.config,
            self.patch_creator_config,
            self.patcher,
            self.patch_creator,
        )

    def log_basic_info(self) -> None:
        """
        Logs basic information.
        """

        width = 100
        log_title = f" {App.APP_NAME} ".center(width, "=")
        self.log.info(f"\n{'=' * width}\n{log_title}\n{'=' * width}")
        self.log.info(f"Program Version: {App.APP_VERSION}")
        self.log.info(f"Executed command: {subprocess.list2cmdline(sys.argv)}")
        self.log.info(f"Current Path: {self.app_path}")
        self.log.info(f"Working Directory: {self.cwd_path}")
        self.log.info(f"Log Path: {self.log_path}")
        self.log.info(
            "Detected Platform: "
            f"{platform.system()} {platform.version()} {platform.architecture()[0]}"
        )

    @override
    def exec(self) -> int:  # type: ignore
        silent: bool = self.config.auto_patch and self.config.silent

        if not silent:
            self.main_window.show()

        retcode: int = super().exec()

        self.log.info("Exiting application...")
        self.clean()

        return retcode

    def clean(self) -> None:
        """
        Cleans up temporary application files.
        """

        self.patcher.clean()
        self.patch_creator.clean()
