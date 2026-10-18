from collections.abc import Mapping
from pathlib import Path
from typing import Any

from settings.config import get_storage_path

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
    return (
        get_storage_path(
            config,
            storage_key=storage_key,
            pipeline_name=SUBWAY_PIPELINE_NAME,
            year=year,
            month=month,
        )
        / SUBWAY_RIDERSHIP_FILENAME
    )
