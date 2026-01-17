"""
Copyright (c) Cutleast
"""

import sys
from argparse import ArgumentParser, Namespace

from app import App


def __init_argparser() -> ArgumentParser:
    """
    Initializes commandline argument parser.
    """

    parser = ArgumentParser(
        prog=sys.executable,
        description=f"{App.APP_NAME} v{App.APP_VERSION} (c) Cutleast "
        "- An automated patcher for UI (swf) files.",
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
        help="Specifies output path for patched files.",
    )
    parser.add_argument(
        "-s",
        "--silent",
        help="Toggles whether the GUI is shown while patching automatically.",
        action="store_true",
    )

    return parser


if __name__ == "__main__":
    parser: ArgumentParser = __init_argparser()
    arg_namespace: Namespace = parser.parse_args()

    sys.exit(App(arg_namespace).exec())
