import re
from collections.abc import Iterator, Mapping
from datetime import date, timedelta
from typing import Any

from active_mobility_pipeline.validation import (
    ACTIVE_MOBILITY_COUNT_SOURCE_FIELDS,
    ACTIVE_MOBILITY_SENSOR_SOURCE_FIELDS,
    ActiveMobilityCountSourceRecord,
    ActiveMobilitySensorSourceRecord,
)
from common.http import RetryPolicy, get_with_retry
from helpers import validate_date_range

SOCRATA_MAX_PAGE_SIZE = 50_000
SOCRATA_RESOURCE_ID_PATTERN = re.compile(r"^[a-z0-9]{4}-[a-z0-9]{4}$")
COUNT_RESULT_ORDER = ("timestamp", "flowid", "granularity")
SENSOR_RESULT_ORDER = ("id", "counters_installationdate")
def _build_dataset_url(
    base_url: str,
    resource_id: str,
    response_format: str,
) -> str:
    normalized_base_url = base_url.strip().rstrip("/")
    normalized_resource_id = resource_id.strip().casefold()
    normalized_format = response_format.strip().casefold()
    if not normalized_base_url:
        raise ValueError("base_url must not be empty")
    if SOCRATA_RESOURCE_ID_PATTERN.fullmatch(normalized_resource_id) is None:
        raise ValueError("resource_id must be a valid Socrata identifier")
    if normalized_format != "json":
        raise ValueError("response_format must be json")
    return f"{normalized_base_url}/{normalized_resource_id}.{normalized_format}"


def _validate_page(page_size: int, offset: int) -> None:
    if isinstance(page_size, bool) or not 1 <= page_size <= SOCRATA_MAX_PAGE_SIZE:
        raise ValueError(f"page_size must be between 1 and {SOCRATA_MAX_PAGE_SIZE}")
    if offset < 0:
        raise ValueError("offset must be greater than or equal to 0")


def _count_query_params(
    *,
    start_date: date,
    end_date: date,
    page_size: int,
    offset: int,
) -> dict[str, str | int]:
    validate_date_range(start_date, end_date)
    _validate_page(page_size, offset)
    try:
        end_exclusive = end_date + timedelta(days=1)
    except OverflowError as error:
        raise ValueError("end_date is outside the supported range") from error
    return {
        "$select": ",".join(ACTIVE_MOBILITY_COUNT_SOURCE_FIELDS),
        "$where": (
            f"timestamp >= '{start_date.isoformat()}T00:00:00.000' AND "
            f"timestamp < '{end_exclusive.isoformat()}T00:00:00.000'"
        ),
        "$order": ",".join(COUNT_RESULT_ORDER),
        "$limit": page_size,
        "$offset": offset,
    }


def _sensor_query_params(
    *,
    page_size: int,
    offset: int,
) -> dict[str, str | int]:
    _validate_page(page_size, offset)
    return {
        "$select": ",".join(ACTIVE_MOBILITY_SENSOR_SOURCE_FIELDS),
        "$order": ",".join(SENSOR_RESULT_ORDER),
        "$limit": page_size,
        "$offset": offset,
    }


def _request_page(
    url: str,
    params: Mapping[str, str | int],
    *,
    timeout_seconds: int,
    app_token: str | None,
    retry_policy: RetryPolicy,
) -> list[dict[str, Any]]:
    headers = None if app_token is None else {"X-App-Token": app_token}
    response = get_with_retry(
        url,
        params=params,
        headers=headers,
        timeout_seconds=timeout_seconds,
        retry_policy=retry_policy,
        request_name="active mobility data",
    )

    payload: Any = response.json()
    if not isinstance(payload, list) or not all(
        isinstance(item, dict) for item in payload
    ):
        raise RuntimeError("Active mobility API response must be a JSON array")
    return payload


def _request_settings(
    *,
    timeout_seconds: int,
    app_token: str | None,
    max_retries: int,
    retry_base_delay_seconds: float,
    retry_max_delay_seconds: float,
) -> tuple[str | None, RetryPolicy]:
    if app_token is not None:
        app_token = app_token.strip()
        if not app_token:
            raise ValueError("app_token must not be blank")
    return app_token, RetryPolicy(
        max_retries=max_retries,
        base_delay_seconds=retry_base_delay_seconds,
        max_delay_seconds=retry_max_delay_seconds,
    )


def iter_active_mobility_counts(
    resource_id: str,
    base_url: str,
    timeout_seconds: int,
    *,
    start_date: date,
    end_date: date,
    response_format: str = "json",
    page_size: int = SOCRATA_MAX_PAGE_SIZE,
    app_token: str | None = None,
    max_retries: int,
    retry_base_delay_seconds: float,
    retry_max_delay_seconds: float,
) -> Iterator[ActiveMobilityCountSourceRecord]:
    url = _build_dataset_url(base_url, resource_id, response_format)
    app_token, retry_policy = _request_settings(
        timeout_seconds=timeout_seconds,
        app_token=app_token,
        max_retries=max_retries,
        retry_base_delay_seconds=retry_base_delay_seconds,
        retry_max_delay_seconds=retry_max_delay_seconds,
    )
    offset = 0
    while True:
        page = _request_page(
            url,
            _count_query_params(
                start_date=start_date,
                end_date=end_date,
                page_size=page_size,
                offset=offset,
            ),
            timeout_seconds=timeout_seconds,
            app_token=app_token,
            retry_policy=retry_policy,
        )
        yield from (
            ActiveMobilityCountSourceRecord.model_validate(record)
            for record in page
        )
        if len(page) < page_size:
            return
        offset += len(page)


def get_active_mobility_sensors(
    resource_id: str,
    base_url: str,
    timeout_seconds: int,
    *,
    response_format: str = "json",
    page_size: int = SOCRATA_MAX_PAGE_SIZE,
    app_token: str | None = None,
    max_retries: int,
    retry_base_delay_seconds: float,
    retry_max_delay_seconds: float,
) -> list[ActiveMobilitySensorSourceRecord]:
    url = _build_dataset_url(base_url, resource_id, response_format)
    app_token, retry_policy = _request_settings(
        timeout_seconds=timeout_seconds,
        app_token=app_token,
        max_retries=max_retries,
        retry_base_delay_seconds=retry_base_delay_seconds,
        retry_max_delay_seconds=retry_max_delay_seconds,
    )
    records: list[ActiveMobilitySensorSourceRecord] = []
    offset = 0
    while True:
        page = _request_page(
            url,
            _sensor_query_params(page_size=page_size, offset=offset),
            timeout_seconds=timeout_seconds,
            app_token=app_token,
            retry_policy=retry_policy,
        )
        records.extend(
            ActiveMobilitySensorSourceRecord.model_validate(record)
            for record in page
        )
        if len(page) < page_size:
            return records
        offset += len(page)
