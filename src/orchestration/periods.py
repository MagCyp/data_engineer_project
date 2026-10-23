from datetime import date, timedelta


def month_range_dates(
    start_month: date,
    end_month: date,
) -> tuple[date, date]:
    """Expand inclusive first-of-month values into an inclusive date range."""
    if start_month.day != 1 or end_month.day != 1:
        raise ValueError("Month values must refer to the first day of a month")
    if start_month > end_month:
        raise ValueError("start_month must be less than or equal to end_month")

    if end_month == date(9999, 12, 1):
        return start_month, date.max
    if end_month.month == 12:
        next_month = date(end_month.year + 1, 1, 1)
    else:
        next_month = date(end_month.year, end_month.month + 1, 1)
    return start_month, next_month - timedelta(days=1)


def year_range_dates(
    start_year: int,
    end_year: int,
) -> tuple[date, date]:
    """Expand an inclusive year range into an inclusive date range."""
    if start_year > end_year:
        raise ValueError("start_year must be less than or equal to end_year")
    return date(start_year, 1, 1), date(end_year, 12, 31)
