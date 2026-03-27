"""Unit tests for SUKL code normalization."""

import pytest

from czechmedmcp.czech.sukl.client import normalize_sukl_code


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("0124137", "0124137"),   # already 7 digits
        ("124137", "0124137"),    # 6 digits → pad
        ("24137", "0024137"),     # 5 digits → pad
        ("0000001", "0000001"),   # edge: all zeros except last
        ("  0124137 ", "0124137"),  # whitespace stripped
        ("1", "0000001"),         # single digit
    ],
)
def test_normalize_sukl_code(raw: str, expected: str) -> None:
    assert normalize_sukl_code(raw) == expected
