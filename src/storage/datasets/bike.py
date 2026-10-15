from collections.abc import Mapping
from pathlib import Path
from typing import Any

from settings.config import get_storage_path

BIKE_COUNTS_FILENAME = "bike_counts.parquet"
BIKE_PIPELINE_NAME = "bike"


def get_bike_counts_path(
    config: Mapping[str, Any],
    *,
    year: int,
    month: int,
    storage_key: str = "bronze_path",
) -> Path:
    """Return the configured year/month bike-count partition path."""
    return (
        get_storage_path(
            config,
            storage_key=storage_key,
            pipeline_name=BIKE_PIPELINE_NAME,
            year=year,
            month=month,
        )
        / BIKE_COUNTS_FILENAME
    )
