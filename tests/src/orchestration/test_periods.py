from datetime import date

import pytest

from orchestration.periods import month_range_dates, year_range_dates


def test_month_range_dates_expands_one_leap_month() -> None:
    assert month_range_dates(date(2024, 2, 1), date(2024, 2, 1)) == (
        date(2024, 2, 1),
        date(2024, 2, 29),
    )


def test_month_range_dates_expands_multiple_months() -> None:
    assert month_range_dates(date(2024, 11, 1), date(2025, 2, 1)) == (
        date(2024, 11, 1),
        date(2025, 2, 28),
    )


def test_month_range_dates_rejects_reversed_range() -> None:
    with pytest.raises(ValueError, match="start_month"):
        month_range_dates(date(2025, 2, 1), date(2025, 1, 1))


def test_year_range_dates_expands_one_year() -> None:
    assert year_range_dates(2025, 2025) == (
        date(2025, 1, 1),
        date(2025, 12, 31),
    )


def test_year_range_dates_expands_multiple_years() -> None:
    assert year_range_dates(2023, 2025) == (
        date(2023, 1, 1),
        date(2025, 12, 31),
    )


def test_year_range_dates_rejects_reversed_range() -> None:
    with pytest.raises(ValueError, match="start_year"):
        year_range_dates(2025, 2024)
