from collections.abc import Mapping
from datetime import date
from typing import Any

from active_mobility_pipeline.ingestion import (
    get_latest_available_date as get_latest_active_mobility_date,
)
from helpers import validate_date_range
from mta_subway_pipeline.ingestion import (
    get_latest_available_date as get_latest_subway_date,
)
from settings import get_pipeline_config

MOBILITY_PIPELINES = ("weather", "active_mobility", "mta_subway")


def _available_from(
    config: Mapping[str, Any],
    pipeline_name: str,
) -> date:
    value = get_pipeline_config(config, pipeline_name).get("available_from")
    if not isinstance(value, str):
        raise ValueError(
            f"Pipeline '{pipeline_name}' must define available_from as a date"
        )
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(
            f"Pipeline '{pipeline_name}' has invalid available_from: {value}"
        ) from error


def validate_mobility_date_range(
    config: Mapping[str, Any],
    *,
    start_date: date,
    end_date: date,
    app_token: str | None = None,
) -> date:
    """Validate an inclusive range shared by every mobility data source."""
    validate_date_range(start_date, end_date)

    common_available_from = max(
        _available_from(config, pipeline_name)
        for pipeline_name in MOBILITY_PIPELINES
    )
    if start_date < common_available_from:
        raise ValueError(
            f"start_date {start_date} precedes the common source boundary "
            f"{common_available_from}"
        )

    active_mobility_date = get_latest_active_mobility_date(
        config,
        app_token=app_token,
    )
    subway_date = get_latest_subway_date(
        config,
        app_token=app_token,
    )
    if active_mobility_date is None:
        raise ValueError("Active mobility dataset contains no data")
    if subway_date is None:
        raise ValueError("Open-ended subway dataset contains no data")

    latest_common_date = min(active_mobility_date, subway_date)
    if end_date > latest_common_date:
        raise ValueError(
            f"end_date {end_date} exceeds the latest common source date "
            f"{latest_common_date} (active mobility: {active_mobility_date}, "
            f"subway: {subway_date})"
        )
    return latest_common_date
