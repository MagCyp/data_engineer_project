import re
from collections.abc import Iterator
from datetime import date, timedelta
from typing import Any

from common.http import RetryPolicy, get_with_retry
from helpers import validate_date_range
from mta_subway_pipeline.validation.models import (
    SUBWAY_SOURCE_FIELDS,
    SubwaySourceRecord,
)

SOCRATA_MAX_PAGE_SIZE = 50_000
SOCRATA_RESOURCE_ID_PATTERN = re.compile(r"^[a-z0-9]{4}-[a-z0-9]{4}$")
SUBWAY_RESULT_ORDER = (
    "transit_timestamp",
    "station_complex_id",
    "transit_mode",
    "payment_method",
    "fare_class_category",
)
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


def _build_query_params(
    *,
    start_date: date,
    end_date: date,
    page_size: int,
    offset: int,
) -> dict[str, str | int]:
    validate_date_range(start_date, end_date)
    if isinstance(page_size, bool) or not 1 <= page_size <= SOCRATA_MAX_PAGE_SIZE:
        raise ValueError(f"page_size must be between 1 and {SOCRATA_MAX_PAGE_SIZE}")
    if offset < 0:
        raise ValueError("offset must be greater than or equal to 0")

    try:
        end_exclusive = end_date + timedelta(days=1)
    except OverflowError as error:
        raise ValueError("end_date is outside the supported range") from error

    start_timestamp = f"{start_date.isoformat()}T00:00:00.000"
    end_timestamp = f"{end_exclusive.isoformat()}T00:00:00.000"

    return {
        "$select": ",".join(SUBWAY_SOURCE_FIELDS),
        "$where": (
            f"transit_timestamp >= '{start_timestamp}' AND "
            f"transit_timestamp < '{end_timestamp}'"
        ),
        "$order": ",".join(SUBWAY_RESULT_ORDER),
        "$limit": page_size,
        "$offset": offset,
    }


def _request_page(
    url: str,
    params: dict[str, str | int],
    timeout_seconds: int,
    app_token: str | None,
    retry_policy: RetryPolicy,
) -> list[SubwaySourceRecord]:
    payload = _request_json_array(
        url,
        params,
        timeout_seconds,
        app_token,
        retry_policy,
    )
    return [SubwaySourceRecord.model_validate(record) for record in payload]


def _request_json_array(
    url: str,
    params: dict[str, str | int],
    timeout_seconds: int,
    app_token: str | None,
    retry_policy: RetryPolicy,
) -> list[Any]:
    headers = None if app_token is None else {"X-App-Token": app_token}
    response = get_with_retry(
        url,
        params=params,
        headers=headers,
        timeout_seconds=timeout_seconds,
        retry_policy=retry_policy,
        request_name="subway data",
    )

    payload: Any = response.json()
    if not isinstance(payload, list):
        raise RuntimeError("Subway API response must be a JSON array")

    return payload


def iter_subway_data(
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
) -> Iterator[SubwaySourceRecord]:
    url = _build_dataset_url(base_url, resource_id, response_format)
    if app_token is not None:
        app_token = app_token.strip()
        if not app_token:
            raise ValueError("app_token must not be blank")
    retry_policy = RetryPolicy(
        max_retries=max_retries,
        base_delay_seconds=retry_base_delay_seconds,
        max_delay_seconds=retry_max_delay_seconds,
    )

    offset = 0
    while True:
        params = _build_query_params(
            start_date=start_date,
            end_date=end_date,
            page_size=page_size,
            offset=offset,
        )
        page = _request_page(
            url,
            params,
            timeout_seconds,
            app_token,
            retry_policy,
        )
        yield from page

        if len(page) < page_size:
            return
        offset += len(page)


def get_subway_data(
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
) -> list[SubwaySourceRecord]:
    return list(
        iter_subway_data(
            resource_id=resource_id,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            start_date=start_date,
            end_date=end_date,
            response_format=response_format,
            page_size=page_size,
            app_token=app_token,
            max_retries=max_retries,
            retry_base_delay_seconds=retry_base_delay_seconds,
            retry_max_delay_seconds=retry_max_delay_seconds,
        )
    )
