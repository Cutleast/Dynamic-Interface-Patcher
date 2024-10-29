"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Optional


def split_path_with_bsa(path: Path) -> tuple[Optional[Path], Optional[Path]]:
    """
    Splits a path containing a BSA file and returns bsa path and file path.

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

    Args:
        path (Path): Path to split.

    Returns:
        tuple[Optional[Path], Optional[Path]]:
            BSA path or None and relative file path or None
    """

    bsa_path: Optional[Path] = None
    file_path: Optional[Path] = None

    parts: list[str] = []

    for part in path.parts:
        parts.append(part)

        if part.endswith(".bsa"):
            bsa_path = Path("/".join(parts))
            parts.clear()

    if parts:
        file_path = Path("/".join(parts))

    return (bsa_path, file_path)
