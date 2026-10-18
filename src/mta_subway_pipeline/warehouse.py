from collections.abc import Mapping
from datetime import date
from typing import Any

from common import load_monthly_partitions
from storage.datasets import get_subway_ridership_path

from .load import load_subway


def load_subway_range(
    config: Mapping[str, Any],
    start_date: date,
    end_date: date,
) -> int:
    """Load monthly Silver subway partitions into PostgreSQL."""
    return load_monthly_partitions(
        start_date,
        end_date,
        path_for_month=lambda year, month: get_subway_ridership_path(
            config,
            year=year,
            month=month,
            storage_key="silver_path",
        ),
        load_partition=load_subway,
        name="subway",
    )
