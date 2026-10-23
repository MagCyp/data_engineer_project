from collections.abc import Iterator, Mapping
from datetime import date
from typing import Any

from active_mobility_pipeline.validation import (
    ActiveMobilityCountSourceRecord,
    ActiveMobilitySensorSourceRecord,
)
from common.socrata import get_latest_socrata_date
from settings import get_api_config, get_pipeline_config

from .client import (
    SOCRATA_DEFAULT_MAX_RETRIES,
    SOCRATA_DEFAULT_RETRY_BASE_DELAY_SECONDS,
    SOCRATA_DEFAULT_RETRY_MAX_DELAY_SECONDS,
    SOCRATA_MAX_PAGE_SIZE,
    get_active_mobility_sensors,
    iter_active_mobility_counts,
)


def _source_settings(
    config: Mapping[str, Any],
    resource_key: str,
) -> tuple[Mapping[str, Any], str]:
    pipeline_config = get_pipeline_config(config, "active_mobility")
    api_name = pipeline_config.get("api")
    if not isinstance(api_name, str) or not api_name.strip():
        raise ValueError("Active mobility pipeline must reference an API")
    resource_id = pipeline_config.get(resource_key)
    if not isinstance(resource_id, str) or not resource_id.strip():
        raise ValueError(
            f"Active mobility pipeline must define {resource_key}"
        )
    return get_api_config(config, api_name), resource_id.strip()


def _request_options(api_config: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "base_url": str(api_config["base_url"]),
        "timeout_seconds": int(api_config["timeout_seconds"]),
        "response_format": str(api_config.get("response_format", "json")),
        "max_retries": api_config.get(
            "max_retries",
            SOCRATA_DEFAULT_MAX_RETRIES,
        ),
        "retry_base_delay_seconds": api_config.get(
            "retry_base_delay_seconds",
            SOCRATA_DEFAULT_RETRY_BASE_DELAY_SECONDS,
        ),
        "retry_max_delay_seconds": api_config.get(
            "retry_max_delay_seconds",
            SOCRATA_DEFAULT_RETRY_MAX_DELAY_SECONDS,
        ),
    }


def iter_count_records(
    config: Mapping[str, Any],
    *,
    start_date: date,
    end_date: date,
    page_size: int = SOCRATA_MAX_PAGE_SIZE,
    app_token: str | None = None,
) -> Iterator[ActiveMobilityCountSourceRecord]:
    api_config, resource_id = _source_settings(config, "counts_resource_id")
    yield from iter_active_mobility_counts(
        resource_id=resource_id,
        start_date=start_date,
        end_date=end_date,
        page_size=page_size,
        app_token=app_token,
        **_request_options(api_config),
    )


def get_latest_available_date(
    config: Mapping[str, Any],
    *,
    app_token: str | None = None,
) -> date | None:
    api_config, resource_id = _source_settings(config, "counts_resource_id")
    return get_latest_socrata_date(
        resource_id=resource_id,
        timestamp_field="timestamp",
        app_token=app_token,
        **_request_options(api_config),
    )


def fetch_sensor_records(
    config: Mapping[str, Any],
    *,
    page_size: int = SOCRATA_MAX_PAGE_SIZE,
    app_token: str | None = None,
) -> list[ActiveMobilitySensorSourceRecord]:
    api_config, resource_id = _source_settings(config, "sensors_resource_id")
    return get_active_mobility_sensors(
        resource_id=resource_id,
        page_size=page_size,
        app_token=app_token,
        **_request_options(api_config),
    )
