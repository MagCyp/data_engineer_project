from collections.abc import Iterable, Mapping
from datetime import date, datetime
from typing import Any

from helpers import validate_month_range
from storage import (
    get_active_mobility_counts_path,
    get_active_mobility_sensors_path,
    merge_and_save_parquet,
    save_as_parquet,
)

from .ingestion import SOCRATA_MAX_PAGE_SIZE, iter_count_records
from .transformations import (
    transform_count_bronze_to_silver,
    transform_count_source_to_bronze,
    transform_sensor_bronze_to_silver,
    transform_sensor_source_to_bronze,
)
from .validation import (
    ActiveMobilitySensorSourceRecord,
    validate_bronze_active_mobility_counts,
    validate_bronze_active_mobility_sensors,
    validate_silver_active_mobility_counts,
    validate_silver_active_mobility_sensors,
)


def process_active_mobility_month(
    config: Mapping[str, Any],
    start_date: date,
    end_date: date,
    *,
    page_size: int = SOCRATA_MAX_PAGE_SIZE,
    app_token: str | None = None,
    ingested_at: datetime | None = None,
) -> None:
    """Download and persist one month of active-mobility counts."""
    validate_month_range(start_date, end_date)
    records = iter_count_records(
        config,
        start_date=start_date,
        end_date=end_date,
        page_size=page_size,
        app_token=app_token,
    )
    bronze = validate_bronze_active_mobility_counts(
        transform_count_source_to_bronze(records, ingested_at=ingested_at)
    )
    merge_and_save_parquet(
        bronze,
        get_active_mobility_counts_path(
            config,
            year=start_date.year,
            month=start_date.month,
            storage_key="bronze_path",
        ),
        key_columns=("flowid", "timestamp", "granularity"),
    )

    silver = validate_silver_active_mobility_counts(
        transform_count_bronze_to_silver(bronze)
    )
    merge_and_save_parquet(
        silver,
        get_active_mobility_counts_path(
            config,
            year=start_date.year,
            month=start_date.month,
            storage_key="silver_path",
        ),
        key_columns=("flow_id", "observed_at_utc", "interval_minutes"),
    )


def process_active_mobility_sensors(
    config: Mapping[str, Any],
    records: Iterable[ActiveMobilitySensorSourceRecord],
    *,
    ingested_at: datetime | None = None,
) -> None:
    """Persist the latest active-mobility sensor metadata snapshot."""
    bronze = validate_bronze_active_mobility_sensors(
        transform_sensor_source_to_bronze(records, ingested_at=ingested_at)
    )
    save_as_parquet(
        bronze,
        get_active_mobility_sensors_path(
            config,
            storage_key="bronze_reference_path",
        ),
    )
    silver = validate_silver_active_mobility_sensors(
        transform_sensor_bronze_to_silver(bronze)
    )
    save_as_parquet(
        silver,
        get_active_mobility_sensors_path(
            config,
            storage_key="silver_reference_path",
        ),
    )
