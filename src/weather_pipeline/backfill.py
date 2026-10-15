from collections.abc import Mapping
from datetime import date
from typing import Any

from helpers import iter_month_ranges
from settings import get_pipeline_config

from .pipeline import process_weather_month


def backfill_weather(
    config: Mapping[str, Any],
    location: str | None = None,
    *,
    start_date: date,
    end_date: date,
) -> None:
    """Process a date range as separate monthly weather partitions."""
    weather_config = get_pipeline_config(config, "weather")
    selected_location = (
        str(weather_config["default_city"])
        if location is None
        else location
    )

    for month_start, month_end in iter_month_ranges(start_date, end_date):
        process_weather_month(
            config,
            selected_location,
            month_start,
            month_end,
        )
