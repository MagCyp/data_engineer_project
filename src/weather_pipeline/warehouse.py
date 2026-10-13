

from collections.abc import Mapping
from datetime import date
from typing import Any

from helpers import iter_month_ranges
from storage.datasets import get_weather_observations_path

from .load import load_weather


def load_weather_range(
    config: Mapping[str, Any],
    location: str,
    start_date: date,
    end_date: date,
) -> int:
    """Load monthly Silver weather partitions into the database."""
    loaded_rows = 0

    for month_start, _ in iter_month_ranges(start_date, end_date):
        silver_path = get_weather_observations_path(
            config,
            location=location,
            year=month_start.year,
            month=month_start.month,
            storage_key="silver_path",
        )
        if not silver_path.is_file():
            raise FileNotFoundError(
                f"Silver weather partition does not exist: {silver_path}"
            )
        loaded_rows += load_weather(silver_path)

    return loaded_rows
