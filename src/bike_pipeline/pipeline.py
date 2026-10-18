from collections.abc import Mapping
from datetime import date, datetime, time
from typing import Any

import polars as pl

from helpers import validate_month_range
from storage import get_bike_counts_path, save_as_parquet

from .transformations import (
    transform_bronze_to_silver,
    transform_source_to_bronze,
)
from .validation import validate_bronze_bike, validate_silver_bike


def process_bike_month(
    config: Mapping[str, Any],
    source_data: pl.DataFrame,
    counter_data: pl.DataFrame,
    start_date: date,
    end_date: date,
    *,
    ingested_at: datetime | None = None,
) -> None:
    """Transform and persist one monthly partition from loaded source data."""
    validate_month_range(start_date, end_date)

    start_at = datetime.combine(start_date, time.min)
    end_at = datetime.combine(end_date, time.max)
    monthly_source = source_data.filter(
        pl.col("date").is_between(start_at, end_at, closed="both")
    )

    bronze = transform_source_to_bronze(
        monthly_source,
        ingested_at=ingested_at,
    )
    validated_bronze = validate_bronze_bike(bronze)
    bronze_path = get_bike_counts_path(
        config,
        year=start_date.year,
        month=start_date.month,
        storage_key="bronze_path",
    )
    save_as_parquet(validated_bronze, bronze_path)

    silver = transform_bronze_to_silver(validated_bronze, counter_data)
    validated_silver = validate_silver_bike(silver)
    silver_path = get_bike_counts_path(
        config,
        year=start_date.year,
        month=start_date.month,
        storage_key="silver_path",
    )
    save_as_parquet(validated_silver, silver_path)
