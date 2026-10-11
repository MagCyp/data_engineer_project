import argparse
from datetime import date

import pytest

from helpers import parse_date


def test_parse_date_returns_date() -> None:
    assert parse_date("2025-01-31") == date(2025, 1, 31)


@pytest.mark.parametrize(
    "value",
    ["31-01-2025", "20250131", "2025-02-29"],
)
def test_parse_date_rejects_invalid_or_non_iso_date(value: str) -> None:
    with pytest.raises(
        argparse.ArgumentTypeError,
        match="Expected YYYY-MM-DD",
    ):
        parse_date(value)
