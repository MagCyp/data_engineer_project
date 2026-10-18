from collections.abc import Mapping
from pathlib import Path
from typing import Any

from settings.config import get_pipeline_config, get_storage_path

from .partitioned import get_partition_file_path

BIKE_COUNTS_FILENAME = "bike_counts.parquet"
BIKE_PIPELINE_NAME = "bike"


def _get_bike_raw_filename(
    config: Mapping[str, Any],
    file_key: str,
) -> str:
    pipeline_config = get_pipeline_config(config, BIKE_PIPELINE_NAME)
    raw_files = pipeline_config.get("raw_files")
    if not isinstance(raw_files, Mapping) or file_key not in raw_files:
        raise ValueError(
            f"Bike raw file '{file_key}' is not configured"
        )

    filename = str(raw_files[file_key])
    if not filename or Path(filename).name != filename:
        raise ValueError(
            f"Bike raw file '{file_key}' must be a file name"
        )
    return filename


def get_bike_raw_counts_path(config: Mapping[str, Any]) -> Path:
    """Return the configured path to the raw bike-count CSV file."""
    return (
        get_storage_path(
            config,
            storage_key="raw_path",
            pipeline_name=BIKE_PIPELINE_NAME,
        )
        / _get_bike_raw_filename(config, "counts")
    )


def get_bike_raw_counters_path(config: Mapping[str, Any]) -> Path:
    """Return the configured path to the raw bike-counter CSV file."""
    return (
        get_storage_path(
            config,
            storage_key="raw_path",
            pipeline_name=BIKE_PIPELINE_NAME,
        )
        / _get_bike_raw_filename(config, "counters")
    )


def get_bike_counts_path(
    config: Mapping[str, Any],
    *,
    year: int,
    month: int,
    storage_key: str = "bronze_path",
) -> Path:
    """Return the configured year/month bike-count partition path."""
    return get_partition_file_path(
        config,
        pipeline_name=BIKE_PIPELINE_NAME,
        filename=BIKE_COUNTS_FILENAME,
        year=year,
        month=month,
        storage_key=storage_key,
    )
