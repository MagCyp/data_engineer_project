from datetime import date
from pathlib import Path

import polars as pl

from .reader import (
    get_ranged_data,
    read_bike_source_file,
    scan_bike_counters_csv,
)


def read_bike_data(
    file_path: str | Path,
    *,
    start_date: date,
    end_date: date,
) -> pl.DataFrame:
    """Read an inclusive date range from the raw bike CSV source."""
    if start_date > end_date:
        raise ValueError("start_date must be less than or equal to end_date")

    query = get_ranged_data(
        read_bike_source_file(file_path),
        start_date,
        end_date,
    )

    try:
        return query.collect(engine="streaming")
    except pl.exceptions.PolarsError as error:
        raise ValueError(f"Invalid bike source data in {file_path}") from error


def read_bike_counter_data(file_path: str | Path) -> pl.DataFrame:
    """Read the small bike-counter metadata file once."""
    try:
        return scan_bike_counters_csv(file_path).collect()
    except pl.exceptions.PolarsError as error:
        raise ValueError(
            f"Invalid bike counter metadata in {file_path}"
        ) from error
