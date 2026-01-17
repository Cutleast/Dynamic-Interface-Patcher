"""
Copyright (c) Cutleast
"""

from argparse import Namespace
from typing import Optional, override

from cutleast_core_lib.base_app import BaseApp
from cutleast_core_lib.core.config.app_config import AppConfig
from cutleast_core_lib.core.utilities.exe_info import get_current_path
from cutleast_core_lib.core.utilities.singleton import Singleton
from PySide6.QtGui import QIcon

import resources_rc as resources_rc
from core.config.config import Config
from core.config.patch_creator_config import PatchCreatorConfig
from core.patch_creator.patch_creator import PatchCreator
from core.patcher.patcher import Patcher
from core.utilities import filesystem as filesystem
from ui.main_window import MainWindow
from ui.utilities.theme_manager import ThemeManager


class App(BaseApp, Singleton):
    """
    Main application class.
    """

    APP_NAME: str = "Dynamic Interface Patcher"
    APP_VERSION: str = "development"

    config: Config
    patch_creator_config: PatchCreatorConfig

    patcher: Patcher
    patch_creator: PatchCreator

    def __init__(self, args: Namespace) -> None:
        Singleton.__init__(self)
        super().__init__(args)

    @override
    def _init(self) -> None:
        self.setApplicationName(App.APP_NAME)
        self.setApplicationDisplayName(f"{App.APP_NAME} v{App.APP_VERSION}")
        self.setApplicationVersion(App.APP_VERSION)
        self.setWindowIcon(QIcon(":/icons/icon.ico"))

        super()._init()

    @override
    def _load_app_config(self) -> AppConfig:
        app_config: AppConfig = AppConfig.load(self.config_path, log_settings=False)
        app_config.accent_color = "#0070e0"
        app_config.log_file_name = "DIP.log"

        self.log_path = get_current_path()

        return app_config

    @override
    def _get_theme_manager(self) -> Optional[ThemeManager]:
        return ThemeManager(self.app_config.accent_color, self.app_config.ui_mode)

    @override
    def _init_main_window(self) -> MainWindow:
        self.config = Config.load(self.config_path, log_settings=False)
        self.config.apply_from_namespace(self.args)
        self.config.print_settings_to_log()
        self.patch_creator_config = PatchCreatorConfig.load(self.res_path / "config")

        self.patcher = Patcher(self.config)
        self.patch_creator = PatchCreator(self.config, self.patch_creator_config)

        return MainWindow(
            logger=self.logger,
            config=self.config,
            patch_creator_config=self.patch_creator_config,
            patcher=self.patcher,
            patch_creator=self.patch_creator,
        )

    @override
    def exec(self) -> int:  # pyright: ignore[reportIncompatibleMethodOverride]
        silent: bool = self.config.auto_patch and self.config.silent

        return super().exec(show_main_window=not silent)

    @override
    def clean(self) -> None:
        super().clean()

        self.patcher.clean()
        self.patch_creator.clean()

    @override
    @classmethod
    def get_repo_owner(cls) -> Optional[str]:
        return

    @override
    @classmethod
    def get_repo_name(cls) -> Optional[str]:
        return

    @override
    @classmethod
    def get_repo_branch(cls) -> Optional[str]:
        return
