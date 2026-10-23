import argparse
from datetime import date

import pytest

from helpers import parse_date, parse_month, parse_year


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


def test_parse_month_returns_first_day() -> None:
    assert parse_month("2025-02") == date(2025, 2, 1)


@pytest.mark.parametrize("value", ["2025-2", "02-2025", "2025-13"])
def test_parse_month_rejects_invalid_value(value: str) -> None:
    with pytest.raises(argparse.ArgumentTypeError, match="Expected YYYY-MM"):
        parse_month(value)


def test_parse_year_returns_integer() -> None:
    assert parse_year("2025") == 2025


@pytest.mark.parametrize("value", ["25", "20250", "20a5", "0000"])
def test_parse_year_rejects_invalid_value(value: str) -> None:
    with pytest.raises(argparse.ArgumentTypeError, match="Expected YYYY"):
        parse_year(value)
