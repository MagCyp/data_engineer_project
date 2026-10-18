from collections.abc import Iterator
from datetime import date, timedelta


def validate_date_range(start_date: date, end_date: date) -> None:
    """Require an inclusive date range in chronological order."""
    if start_date > end_date:
        raise ValueError("start_date must be less than or equal to end_date")


def validate_month_range(start_date: date, end_date: date) -> None:
    """Require a valid date range contained within one calendar month."""
    validate_date_range(start_date, end_date)
    if (start_date.year, start_date.month) != (end_date.year, end_date.month):
        raise ValueError("start_date and end_date must belong to the same month")


def iter_month_ranges(
    start_date: date,
    end_date: date,
) -> Iterator[tuple[date, date]]:
    """Yield (start, end) tuples for each month in the range."""
    validate_date_range(start_date, end_date)

    current_date = start_date

    while current_date <= end_date:
        next_month = (current_date.month % 12) + 1
        next_year = current_date.year + (current_date.month // 12)
        next_month_start = date(next_year, next_month, 1)
        month_end = min(next_month_start - timedelta(days=1), end_date)
        yield current_date, month_end
        current_date = next_month_start
