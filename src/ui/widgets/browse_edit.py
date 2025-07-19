"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Any, Optional, override

import qtawesome as qta
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLineEdit, QPushButton


class BrowseLineEdit(QLineEdit):
    """
    Custom QLineEdit with a "Browse" button to open a QFileDialog.
    """

    __base_path: Optional[Path]
    __browse_button: QPushButton
    __file_dialog: QFileDialog

    pathChanged = Signal(str, str)
    """
    This signal gets emitted when a file is selected in the QFileDialog.
    It emits the current text and the selected file.

    Args:
        str: Current path
        str: New path
    """

    def __init__(
        self,
        initial_path: Optional[Path] = None,
        base_path: Optional[Path] = None,
        *args: Any,
        **kwargs: dict[str, Any],
    ) -> None:
        """
        Args:
            initial_path (Optional[Path], optional):
                Initial path to display. Defaults to None.
            base_path (Optional[Path], optional):
                Base path for relative paths. Defaults to None.
        """

        super().__init__(*args, **kwargs)

        self.__base_path = base_path

        self.__init_ui()

        if initial_path is not None:
            self.setPath(initial_path)

    def __init_ui(self) -> None:
        self.__file_dialog = QFileDialog()

        hlayout: QHBoxLayout = QHBoxLayout(self)
        hlayout.setContentsMargins(0, 0, 0, 0)

        # Push Browse Button to the right-hand side
        hlayout.addStretch()

        self.__browse_button = QPushButton()
        self.__browse_button.setIcon(qta.icon("fa5s.folder-open", color="#ffffff"))
        self.__browse_button.clicked.connect(self.__browse)
        self.__browse_button.setCursor(Qt.CursorShape.ArrowCursor)
        hlayout.addWidget(self.__browse_button)

    def configureFileDialog(self, *args: Any, **kwargs: dict[str, Any]) -> None:
        """
        Redirects `args` and `kwargs` to constructor of `QFileDialog`.
        """

        self.__file_dialog = QFileDialog(*args, **kwargs)

    def setFileMode(self, mode: QFileDialog.FileMode) -> None:
        """
        Redirects `mode` to `QFileDialog.setFileMode()`.
        """

        self.__file_dialog.setFileMode(mode)

    def setNameFilters(self, filters: list[str]) -> None:
        """
        Redirects `filters` to `QFileDialog.setNameFilters()`.
        """

        self.__file_dialog.setNameFilters(filters)

    @override
    def setText(self, text: Optional[str]) -> None:
        old_text: str = self.text()
        super().setText(text)
        self.pathChanged.emit(old_text, text or "")

    def getPath(self, absolute: bool = False) -> Optional[Path]:
        """
        Returns the current path.

        Args:
            absolute (bool, optional):
                Whether to join the path with the base path, if any. Defaults to False.

        Returns:
            Optional[Path]: Current path or None if empty
        """

        if not self.text().strip():
            return

        if absolute and self.__base_path is not None:
            return self.__base_path.joinpath(self.text())

        return Path(self.text())

    def setPath(self, path: Path) -> None:
        """
        Sets the current path.

        Args:
            path (Path): New path
        """

        current_text: str = self.text().strip()

        if self.__base_path is not None and path.is_relative_to(self.__base_path):
            self.setText(str(path.relative_to(self.__base_path)))
        else:
            self.setText(str(path))

        self.pathChanged.emit(current_text, str(path))

    def __browse(self) -> None:
        current_path: Optional[Path] = self.getPath(absolute=True)

        if current_path is not None:
            self.__file_dialog.setDirectory(str(current_path.parent))
            self.__file_dialog.selectFile(current_path.name)

        if self.__file_dialog.exec():
            selected_files: list[str] = self.__file_dialog.selectedFiles()

            if selected_files:
                file: Path = Path(selected_files.pop())

                self.setPath(file)


def test() -> None:
    from PySide6.QtWidgets import QApplication

    app = QApplication()

    edit = BrowseLineEdit()
    edit.setFileMode(QFileDialog.FileMode.AnyFile)
    edit.show()

    app.exec()


if __name__ == "__main__":
    test()
