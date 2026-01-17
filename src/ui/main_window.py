"""
Copyright (c) Cutleast
"""

from typing import override

from cutleast_core_lib.core.utilities.logger import Logger
from cutleast_core_lib.ui.widgets.about_dialog import AboutDialog
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox

from core.config.config import Config
from core.config.patch_creator_config import PatchCreatorConfig
from core.patch_creator.patch_creator import PatchCreator
from core.patcher.patcher import Patcher
from core.utilities.licenses import LICENSES

from .main_widget import MainWidget
from .menubar import MenuBar
from .statusbar import StatusBar


class MainWindow(QMainWindow):
    """
    Class for main patcher window.
    """

    __menu_bar: MenuBar
    __main_widget: MainWidget

    def __init__(
        self,
        logger: Logger,
        config: Config,
        patch_creator_config: PatchCreatorConfig,
        patcher: Patcher,
        patch_creator: PatchCreator,
    ) -> None:
        super().__init__()

        self.resize(1000, 600)

        self.__init_ui(logger, config, patch_creator_config, patcher, patch_creator)

        self.__menu_bar.exit_signal.connect(self.close)
        self.__menu_bar.about_signal.connect(self.__show_about)
        self.__menu_bar.about_qt_signal.connect(self.__show_about_qt)

    def __init_ui(
        self,
        logger: Logger,
        config: Config,
        patch_creator_config: PatchCreatorConfig,
        patcher: Patcher,
        patch_creator: PatchCreator,
    ) -> None:
        self.__init_menu_bar()
        self.__init_main_widget(
            logger, config, patch_creator_config, patcher, patch_creator
        )
        self.__init_status_bar()

    def __init_menu_bar(self) -> None:
        self.__menu_bar = MenuBar()
        self.setMenuBar(self.__menu_bar)

    def __init_main_widget(
        self,
        logger: Logger,
        config: Config,
        patch_creator_config: PatchCreatorConfig,
        patcher: Patcher,
        patch_creator: PatchCreator,
    ) -> None:
        self.__main_widget = MainWidget(
            logger, config, patch_creator_config, patcher, patch_creator
        )
        self.setCentralWidget(self.__main_widget)

    def __init_status_bar(self) -> None:
        self.__status_bar = StatusBar()
        self.setStatusBar(self.__status_bar)

    @override
    def closeEvent(self, event: QCloseEvent) -> None:
        event.ignore()

        if self.__main_widget.close():
            QApplication.quit()

    def __show_about(self) -> None:
        from app import App

        AboutDialog(
            app_name=App.APP_NAME,
            app_version=App.APP_VERSION,
            app_icon=App.get().windowIcon(),
            app_license="GNU General Public License v3.0",
            licenses=LICENSES,
            parent=self,
        ).exec()

    def __show_about_qt(self) -> None:
        QMessageBox.aboutQt(self, self.tr("About Qt"))
