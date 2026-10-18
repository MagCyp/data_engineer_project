from collections.abc import Mapping
from datetime import UTC, date, datetime
from typing import Any

from helpers import iter_month_ranges, validate_date_range

from .ingestion import SOCRATA_MAX_PAGE_SIZE
from .pipeline import process_subway_month


def backfill_subway(
    config: Mapping[str, Any],
    *,
    start_date: date,
    end_date: date,
    page_size: int = SOCRATA_MAX_PAGE_SIZE,
    app_token: str | None = None,
) -> None:
    """Download and write all requested monthly subway partitions."""
    validate_date_range(start_date, end_date)

    ingested_at = datetime.now(UTC)
    for month_start, month_end in iter_month_ranges(start_date, end_date):
        process_subway_month(
            config,
            month_start,
            month_end,
            page_size=page_size,
            app_token=app_token,
            ingested_at=ingested_at,
        )
