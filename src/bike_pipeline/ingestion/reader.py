import csv
from datetime import date, datetime, time
from pathlib import Path

import polars as pl

from bike_pipeline.validation.models import (
    BIKE_COUNTER_SOURCE_COLUMNS,
    BIKE_COUNTER_SOURCE_SCHEMA,
    BIKE_RAW_CSV_SCHEMA,
    BIKE_SOURCE_COLUMNS,
    BIKE_SOURCE_DATETIME_FORMAT,
    BIKE_SOURCE_SCHEMA,
)


def _validate_source_file(
    file_path: str | Path,
    *,
    expected_columns: tuple[str, ...],
) -> Path:
    if not str(file_path).strip():
        raise ValueError("Bike source file path must not be empty")

    path = Path(file_path)
    if path.suffix.casefold() != ".csv":
        raise ValueError(f"Unsupported bike source format: {path.suffix}")
    if not path.is_file():
        raise FileNotFoundError(f"Bike source file does not exist: {path}")

    _validate_header(path, expected_columns=expected_columns)
    return path


def _validate_header(
    file_path: Path,
    *,
    expected_columns: tuple[str, ...],
) -> None:
    with file_path.open(encoding="utf-8-sig", newline="") as source_file:
        header = next(csv.reader(source_file), None)

    if header is None:
        raise ValueError(f"Bike source file is empty: {file_path}")
    if tuple(header) != expected_columns:
        raise ValueError(
            "Bike source columns do not match the expected columns. "
            f"Expected: {list(expected_columns)}, got: {header}"
        )


def scan_bike_csv(file_path: str | Path) -> pl.LazyFrame:
    """Validate and lazily scan a raw bike CSV file."""
    path = _validate_source_file(
        file_path,
        expected_columns=BIKE_SOURCE_COLUMNS,
    )
    return pl.scan_csv(
        path,
        schema=BIKE_RAW_CSV_SCHEMA,
        low_memory=True,
        glob=False,
    ).with_columns(
        pl.col("counts")
        .str.replace_all(",", "")
        .cast(BIKE_SOURCE_SCHEMA["counts"])
    )


def scan_bike_counters_csv(file_path: str | Path) -> pl.LazyFrame:
    """Validate and lazily scan the bike counter metadata CSV file."""
    path = _validate_source_file(
        file_path,
        expected_columns=BIKE_COUNTER_SOURCE_COLUMNS,
    )
    return pl.scan_csv(
        path,
        schema=BIKE_COUNTER_SOURCE_SCHEMA,
        low_memory=True,
        glob=False,
    )


def read_bike_source_file(file_path: str | Path) -> pl.LazyFrame:
    """Return a validated lazy scan of a raw bike CSV file."""
    return scan_bike_csv(file_path)


def get_ranged_data(
    lazy_frame: pl.LazyFrame,
    start_date: date,
    end_date: date,
) -> pl.LazyFrame:
    """Parse source timestamps and filter an inclusive calendar-date range."""
    if start_date > end_date:
        raise ValueError("start_date must be less than or equal to end_date")

    start_at = datetime.combine(start_date, time.min)
    end_at = datetime.combine(end_date, time.max)
    return lazy_frame.with_columns(
        pl.col("date").str.strptime(
            pl.Datetime(time_unit="us"),
            format=BIKE_SOURCE_DATETIME_FORMAT,
            strict=True,
        )
    ).filter(
        pl.col("date").is_between(start_at, end_at, closed="both")
    )
