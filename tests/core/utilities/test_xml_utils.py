"""
Copyright (c) Cutleast
"""

import pytest

from core.utilities.xml_utils import parse_xpath_part

XPATH_PARTS_DATA: list[tuple[str, tuple[str, dict[str, str]]]] = [
    (
        "/test[@attr='val'][@attr2='val2']",
        ("test", {"attr": "val", "attr2": "val2"}),
    ),
    (
        "test[@attr='val'][@attr2='val2']",
        ("test", {"attr": "val", "attr2": "val2"}),
    ),
    ("test", ("test", {})),
]


@pytest.mark.parametrize("xpath_part, expected_result", XPATH_PARTS_DATA)
def test_parse_xpath(
    xpath_part: str, expected_result: tuple[str, dict[str, str]]
) -> None:
    """
    Tests the parsing of an XPath part.
    """

    # when
    actual_result: tuple[str, dict[str, str]] = parse_xpath_part(xpath_part)

    # then
    assert actual_result == expected_result
