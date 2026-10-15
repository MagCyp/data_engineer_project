from collections.abc import Mapping
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from helpers import iter_month_ranges

from .ingestion import read_bike_counter_data, read_bike_data
from .pipeline import process_bike_month


def backfill_bike(
    config: Mapping[str, Any],
    counts_file_path: str | Path,
    counters_file_path: str | Path,
    *,
    start_date: date,
    end_date: date,
) -> None:
    """Read the source once and write all requested monthly partitions."""
    if start_date > end_date:
        raise ValueError("start_date must be less than or equal to end_date")

    # The 400+ MB counts CSV is scanned and collected exactly once for the
    # complete backfill range. Monthly processing below only filters this
    # in-memory frame and never reopens the source file.
    source_data = read_bike_data(
        counts_file_path,
        start_date=start_date,
        end_date=end_date,
    )
    counter_data = read_bike_counter_data(counters_file_path)
    ingested_at = datetime.now(UTC)

    for month_start, month_end in iter_month_ranges(start_date, end_date):
        process_bike_month(
            config,
            source_data,
            counter_data,
            month_start,
            month_end,
            ingested_at=ingested_at,
        )
