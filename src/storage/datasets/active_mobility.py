from collections.abc import Mapping
from pathlib import Path
from typing import Any

from settings import get_storage_path

from .partitioned import get_partition_file_path

ACTIVE_MOBILITY_COUNTS_FILENAME = "active_mobility_counts.parquet"
ACTIVE_MOBILITY_PIPELINE_NAME = "active_mobility"
ACTIVE_MOBILITY_SENSORS_FILENAME = "active_mobility_sensors.parquet"


def get_active_mobility_counts_path(
    config: Mapping[str, Any],
    *,
    year: int,
    month: int,
    storage_key: str = "bronze_path",
) -> Path:
    """Return the configured monthly active-mobility counts path."""
    return get_partition_file_path(
        config,
        pipeline_name=ACTIVE_MOBILITY_PIPELINE_NAME,
        filename=ACTIVE_MOBILITY_COUNTS_FILENAME,
        year=year,
        month=month,
        storage_key=storage_key,
    )


def get_active_mobility_sensors_path(
    config: Mapping[str, Any],
    *,
    storage_key: str = "bronze_reference_path",
) -> Path:
    """Return the configured active-mobility sensor snapshot path."""
    return (
        get_storage_path(
            config,
            storage_key=storage_key,
            pipeline_name=ACTIVE_MOBILITY_PIPELINE_NAME,
        )
        / ACTIVE_MOBILITY_SENSORS_FILENAME
    )
