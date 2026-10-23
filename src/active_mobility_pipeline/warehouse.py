from collections.abc import Mapping
from datetime import date
from typing import Any

from common import load_monthly_partitions
from storage import (
    get_active_mobility_counts_path,
    get_active_mobility_sensors_path,
)

from .load import load_active_mobility_counts, load_active_mobility_sensors


def load_active_mobility_range(
    config: Mapping[str, Any],
    start_date: date,
    end_date: date,
) -> int:
    """Load sensor metadata and monthly counts into PostgreSQL."""
    sensor_rows = load_active_mobility_sensors(
        get_active_mobility_sensors_path(
            config,
            storage_key="silver_reference_path",
        )
    )
    count_rows = load_monthly_partitions(
        start_date,
        end_date,
        path_for_month=lambda year, month: get_active_mobility_counts_path(
            config,
            year=year,
            month=month,
            storage_key="silver_path",
        ),
        load_partition=load_active_mobility_counts,
        name="active mobility",
    )
    return sensor_rows + count_rows
