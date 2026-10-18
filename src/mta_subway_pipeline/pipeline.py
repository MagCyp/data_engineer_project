from collections.abc import Mapping
from datetime import date, datetime
from typing import Any

from storage import get_subway_ridership_path, save_as_parquet

from .ingestion import SOCRATA_MAX_PAGE_SIZE, iter_subway_records
from .transformations import (
    transform_bronze_to_silver,
    transform_source_to_bronze,
)
from .validation import validate_bronze_subway, validate_silver_subway


def process_subway_month(
    config: Mapping[str, Any],
    start_date: date,
    end_date: date,
    *,
    page_size: int = SOCRATA_MAX_PAGE_SIZE,
    app_token: str | None = None,
    ingested_at: datetime | None = None,
) -> None:
    """Download, transform, validate, and persist one subway month."""
    if start_date > end_date:
        raise ValueError("start_date must be less than or equal to end_date")
    if (start_date.year, start_date.month) != (end_date.year, end_date.month):
        raise ValueError("start_date and end_date must belong to the same month")

    records = iter_subway_records(
        config,
        start_date=start_date,
        end_date=end_date,
        page_size=page_size,
        app_token=app_token,
    )
    bronze = transform_source_to_bronze(records, ingested_at=ingested_at)
    validated_bronze = validate_bronze_subway(bronze)
    bronze_path = get_subway_ridership_path(
        config,
        year=start_date.year,
        month=start_date.month,
        storage_key="bronze_path",
    )
    save_as_parquet(validated_bronze, bronze_path)

    silver = transform_bronze_to_silver(validated_bronze)
    validated_silver = validate_silver_subway(silver)
    silver_path = get_subway_ridership_path(
        config,
        year=start_date.year,
        month=start_date.month,
        storage_key="silver_path",
    )
    save_as_parquet(validated_silver, silver_path)
