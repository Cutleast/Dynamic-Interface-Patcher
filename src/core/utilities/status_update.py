"""
Copyright (c) Cutleast
"""

from enum import Enum, auto


class StatusUpdate(Enum):
    """
    Enum for status updates, transmitted via Qt signals.
    """

    Ready = auto()
    """
    When Patcher or Patch Creator are ready.
    """

    Running = auto()
    """
    When Patcher or Patch Creator are running.
    """

    Failed = auto()
    """
    When Patcher or Patch Creator failed.
    """

    Successful = auto()
    """
    When Patcher or Patch Creator succeeded.
    """
