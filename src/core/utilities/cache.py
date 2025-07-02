"""
Copyright (c) Cutleast

Wrapper for `functools.cache`
"""

import functools
from typing import Callable, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


def cache(func: Callable[P, R]) -> Callable[P, R]:
    """
    Wrapper for `functools.cache` to maintain Python >3.12 type annotations
    for static type checkers like mypy.

    Returns:
        Callable[P, R]: wrapped function
    """

    wrapped: Callable[P, R] = functools.cache(func)  # type: ignore[attr-defined]

    return wrapped
