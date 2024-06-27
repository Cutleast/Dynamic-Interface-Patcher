"""
Part of Dynamic Interface Patcher (DIP).
Contains utility classes and functions.

Licensed under Attribution-NonCommercial-NoDerivatives 4.0 International
"""

import logging
import ctypes
import subprocess
import sys
import xml.dom.minidom
from pathlib import Path
from typing import Callable

import psutil
import qtpy.QtCore as qtc
import qtpy.QtGui as qtg
import qtpy.QtWidgets as qtw


class Thread(qtc.QThread):
    """
    Proxy class for QThread.
    Takes a callable function or method
    as additional parameter
    that is executed in the QThread.
    """

    def __init__(self, target: Callable, name: str = None, parent: qtw.QWidget = None):
        super().__init__(parent)

        self.target = target

        if name is not None:
            self.setObjectName(name)

    def run(self):
        self.target()

    def __repr__(self):
        return self.objectName()

    def __str__(self):
        return self.objectName()


class StdoutHandler(qtc.QObject):
    """
    Redirector class for sys.stdout.

    Redirects sys.stdout to self.output_signal [QtCore.Signal].
    """

    output_signal = qtc.Signal(object)

    def __init__(self, parent: qtc.QObject):
        super().__init__(parent)

        self._stream = sys.stdout
        sys.stdout = self
        self._content = ""

    def write(self, text: str):
        self._stream.write(text)
        self._content += text
        self.output_signal.emit(text)

    def __getattr__(self, name: str):
        return getattr(self._stream, name)

    def __del__(self):
        try:
            sys.stdout = self._stream
        except AttributeError:
            pass


def hex_to_rgb(value: str):
    """
    Converts hexadecimal color values
    to a tuple containing the values in rgb.
    """

    value = value.lstrip("#")
    length = len(value)
    return tuple(
        int(value[i : i + length // 3], 16) for i in range(0, length, length // 3)
    )


def lower_dict(nested_dict: dict):
    new_dict = {}

    for key, value in nested_dict.items():
        if isinstance(value, dict):
            new_dict[key] = lower_dict(value)
        elif isinstance(value, str):
            new_dict[key] = value.lower()
        else:
            new_dict[key] = value

    return new_dict


def apply_dark_title_bar(widget: qtw.QWidget):
    """
    Applies dark title bar to <widget>.


    More information here:

    https://docs.microsoft.com/en-us/windows/win32/api/dwmapi/ne-dwmapi-dwmwindowattribute
    """

    DWMWA_USE_IMMERSIVE_DARK_MODE = 20
    set_window_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
    hwnd = widget.winId()
    rendering_policy = DWMWA_USE_IMMERSIVE_DARK_MODE
    value = 2
    value = ctypes.c_int(value)
    set_window_attribute(
        hwnd, rendering_policy, ctypes.byref(value), ctypes.sizeof(value)
    )


def kill_child_process(parent_pid: int):
    """
    Kills process with <parent_pid> and all its children.
    """

    parent = psutil.Process(parent_pid)
    for child in parent.children(recursive=True):
        child.kill()
    parent.kill()


def check_java():
    """
    Checks if java is installed and accessable from PATH.
    """

    try:
        subprocess.check_call(
            ["java", "-version"],
            shell=True,
            stdout=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def parse_path(path: Path):
    """
    Parses path and returns tuple with
    two components:
    bsa path and file path

    For example:
    ```
    path = 'C:/Modding/RaceMenu/RaceMenu.bsa/interface/racesex_menu.swf'
    ```
    ==>
    ```
    (
        'C:/Modding/RaceMenu/RaceMenu.bsa',
        'interface/racesex_menu.swf'
    )
    ```
    """

    bsa_path = file_path = None

    parts: list[str] = []

    for part in path.parts:
        parts.append(part)

        if part.endswith(".bsa"):
            bsa_path = Path("/".join(parts))
            parts.clear()
    if parts:
        file_path = Path("/".join(parts))

    return (bsa_path, file_path)


def process_patch_data(patch_data: dict):
    result: list[dict[str, str | dict]] = []

    def process_data(data: dict | list, cur_filter: str = ""):
        cur_result: dict[str, str | dict] = {}
        cur_changes: dict[str, str] = {}

        if isinstance(data, list):
            for item in data:
                if child_result := process_data(item, cur_filter + "/item"):
                    result.append(child_result)

        else:
            for key, value in data.items():
                if isinstance(value, str):
                    if key.startswith("#"):
                        attribute = key.removeprefix("#")
                        # Fix frames
                        if attribute == "frameId":
                            cur_filter, _ = cur_filter.rsplit("/", 1)
                            cur_filter += "/frame"
                        cur_filter += f"[@{attribute}='{value}']"
                    else:
                        attribute = key.removeprefix("~")
                        cur_changes[attribute] = value

                    if cur_filter and cur_changes:
                        cur_result = {"filter": cur_filter, "changes": cur_changes}
                else:
                    if child_result := process_data(value, cur_filter + f"/{key}"):
                        result.append(child_result)

        return cur_result

    if cur_result := process_data(patch_data):
        result.append(cur_result)

    return result


def beautify_xml(xml_string: str):
    dom = xml.dom.minidom.parseString(xml_string)
    pretty_xml_as_string = dom.toprettyxml()

    lines = pretty_xml_as_string.splitlines()
    lines = [line + "\n" for line in lines if line.strip()]

    return "".join(lines)


def get_list_widget_items(list_widget: qtw.QListWidget):
    """
    Returns items from <list_widget> in order.
    """

    return [list_widget.item(x).text() for x in range(list_widget.count())]


def get_combobox_items(combo_box: qtw.QComboBox):
    """
    Returns items from <combo_box> in order.
    """

    return [combo_box.itemText(x) for x in range(combo_box.count())]


def extract_archive(archive: Path, dest: Path):
    """
    Extracts all files from `archive` to `dest`.
    """

    log = logging.getLogger("ArchiveExtractor")

    cmd = ["7z.exe", "x", str(archive), f"-o{dest}", "-aoa", "-y"]

    with subprocess.Popen(
        cmd,
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf8",
        errors="ignore",
    ) as process:
        output = process.stderr.read()

    if process.returncode:
        log.debug(f"Command: {cmd}")
        log.error(output)
        raise Exception("Unpacking command failed!")
