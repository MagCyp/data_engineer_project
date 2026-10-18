

from collections.abc import Mapping
from datetime import date
from typing import Any

from common import load_monthly_partitions
from storage.datasets import get_weather_observations_path

from .load import load_weather


def load_weather_range(
    config: Mapping[str, Any],
    location: str,
    start_date: date,
    end_date: date,
) -> int:
    """Load monthly Silver weather partitions into the database."""
    return load_monthly_partitions(
        start_date,
        end_date,
        path_for_month=lambda year, month: get_weather_observations_path(
            config,
            location=location,
            year=year,
            month=month,
            storage_key="silver_path",
        ),
        load_partition=load_weather,
        name="weather",
    )
