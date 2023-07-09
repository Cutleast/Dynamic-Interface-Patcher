"""
Part of Dynamic Interface Patcher (DIP).
Contains utility classes and functions.

Licensed under Attribution-NonCommercial-NoDerivatives 4.0 International
"""

import ctypes
import psutil
import sys
import subprocess
from typing import Callable, List, Dict
from pathlib import Path

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

    value = value.lstrip('#')
    length = len(value)
    return tuple(int(value[i:i + length // 3], 16) for i in range(0, length, length // 3))

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
        hwnd,
        rendering_policy,
        ctypes.byref(value),
        ctypes.sizeof(value)
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
            stderr=subprocess.DEVNULL
        )
        return True
    except subprocess.CalledProcessError:
        return False

def parse_path(path: Path):
    """
    Parses path in returns tuple with
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

    parts: List[str] = []

    for part in path.parts:
        parts.append(part)

        if part.endswith(".bsa"):
            bsa_path = Path("/".join(parts))
            parts.clear()
    if parts:
        file_path = Path("/".join(parts))

    return (bsa_path, file_path)

def process_patch_data(
        patch_data,
        pre_result: Dict[str, dict] = {},
        pre_filters: str = "",
        pre_changes: dict = {}
    ):
        cur_result = pre_result

        if isinstance(patch_data, dict):
            cur_filters = (pre_filters + "/item") if pre_filters.endswith("]") else pre_filters
            cur_changes = pre_changes

            for key, value in patch_data.items():
                if key.startswith("#"): # filters
                    cur_filters += f"[@{key.removeprefix('#')}='{str(value)}']"

                elif key.startswith("~"): # attributes
                    cur_changes[key.removeprefix('~')] = value

                elif (not isinstance(value, str)): # children
                    if not cur_filters.endswith("]"):
                        cur_filters = cur_filters.removesuffix(cur_filters.split("/")[-1])
                        cur_filters = cur_filters.removesuffix("/")
                    cur_filters = f"{cur_filters}/{key}"
                    process_patch_data(value, cur_result, cur_filters, {})

            if cur_filters and cur_changes:
                cur_filters = cur_filters.removesuffix("/item")
                if cur_result:
                    cur_filters = cur_filters.removeprefix(list(cur_result.keys())[0])
                if cur_filters in cur_result:
                    print(f"WARNING! Filter '{cur_filters}' does already exist! Overwriting...")
                cur_result[cur_filters] = cur_changes

        elif isinstance(patch_data, list):
            pre_filters += "/item"
            for item in patch_data:
                process_patch_data(item, cur_result, pre_filters, {})

        return cur_result
