from collections.abc import Mapping
from datetime import date
from typing import Any

from helpers import iter_month_ranges
from storage.datasets import get_subway_ridership_path

from .load import load_subway


def load_subway_range(
    config: Mapping[str, Any],
    start_date: date,
    end_date: date,
) -> int:
    """Load monthly Silver subway partitions into PostgreSQL."""
    if start_date > end_date:
        raise ValueError("start_date must be less than or equal to end_date")

    loaded_rows = 0
    for month_start, _ in iter_month_ranges(start_date, end_date):
        silver_path = get_subway_ridership_path(
            config,
            year=month_start.year,
            month=month_start.month,
            storage_key="silver_path",
        )
        if not silver_path.is_file():
            raise FileNotFoundError(
                f"Silver subway partition does not exist: {silver_path}"
            )
        loaded_rows += load_subway(silver_path)

    return loaded_rows
