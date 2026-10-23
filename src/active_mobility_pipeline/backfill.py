from collections.abc import Mapping
from datetime import UTC, date, datetime
from typing import Any

from helpers import iter_month_ranges, validate_date_range

from .ingestion import SOCRATA_MAX_PAGE_SIZE, fetch_sensor_records
from .pipeline import (
    process_active_mobility_month,
    process_active_mobility_sensors,
)


def backfill_active_mobility(
    config: Mapping[str, Any],
    *,
    start_date: date,
    end_date: date,
    page_size: int = SOCRATA_MAX_PAGE_SIZE,
    app_token: str | None = None,
) -> None:
    """Download and write active-mobility sensor and count data."""
    validate_date_range(start_date, end_date)
    ingested_at = datetime.now(UTC)
    sensor_records = fetch_sensor_records(
        config,
        page_size=page_size,
        app_token=app_token,
    )
    process_active_mobility_sensors(
        config,
        sensor_records,
        ingested_at=ingested_at,
    )

    for month_start, month_end in iter_month_ranges(start_date, end_date):
        process_active_mobility_month(
            config,
            month_start,
            month_end,
            page_size=page_size,
            app_token=app_token,
            ingested_at=ingested_at,
        )
