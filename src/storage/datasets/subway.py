from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .partitioned import get_partition_file_path

SUBWAY_RIDERSHIP_FILENAME = "subway_ridership.parquet"
SUBWAY_PIPELINE_NAME = "mta_subway"


def get_subway_ridership_path(
    config: Mapping[str, Any],
    *,
    year: int,
    month: int,
    storage_key: str = "bronze_path",
) -> Path:
    """Return the configured year/month subway partition path."""
    return get_partition_file_path(
        config,
        pipeline_name=SUBWAY_PIPELINE_NAME,
        filename=SUBWAY_RIDERSHIP_FILENAME,
        year=year,
        month=month,
        storage_key=storage_key,
    )
