from datetime import date, timedelta


def iter_month_ranges(
    start_date: date,
    end_date: date,
):
    """Yield (start, end) tuples for each month in the range."""
    if start_date > end_date:
        raise ValueError("start_date must be less than or equal to end_date")

    current_date = start_date.replace(day=1)

    while current_date <= end_date:
        next_month = (current_date.month % 12) + 1
        next_year = current_date.year + (current_date.month // 12)
        next_month_start = date(next_year, next_month, 1)
        month_end = min(next_month_start - timedelta(days=1), end_date)
        yield (current_date, month_end)
        current_date = next_month_start
