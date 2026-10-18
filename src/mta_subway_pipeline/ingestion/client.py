import re
import time
from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Any

import httpx

from mta_subway_pipeline.validation.models import (
    SUBWAY_SOURCE_FIELDS,
    SubwaySourceRecord,
)

SOCRATA_MAX_PAGE_SIZE = 50_000
SOCRATA_DEFAULT_MAX_RETRIES = 3
SOCRATA_DEFAULT_RETRY_BASE_DELAY_SECONDS = 1.0
SOCRATA_DEFAULT_RETRY_MAX_DELAY_SECONDS = 60.0
SOCRATA_RETRYABLE_STATUS_CODES = frozenset({429, 502, 503, 504})
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
    if start_date > end_date:
        raise ValueError("start_date must be before or equal to end_date")
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
    max_retries: int,
    retry_base_delay_seconds: float,
    retry_max_delay_seconds: float,
) -> list[SubwaySourceRecord]:
    for retry_number in range(max_retries + 1):
        try:
            if app_token is None:
                response = httpx.get(
                    url,
                    params=params,
                    timeout=timeout_seconds,
                )
            else:
                response = httpx.get(
                    url,
                    params=params,
                    headers={"X-App-Token": app_token},
                    timeout=timeout_seconds,
                )
        except httpx.RequestError as error:
            if retry_number < max_retries:
                time.sleep(
                    _retry_delay_seconds(
                        retry_number=retry_number,
                        base_delay_seconds=retry_base_delay_seconds,
                        max_delay_seconds=retry_max_delay_seconds,
                    )
                )
                continue
            raise RuntimeError(
                f"An error occurred while requesting subway data: {error}"
            ) from error

        if (
            response.status_code in SOCRATA_RETRYABLE_STATUS_CODES
            and retry_number < max_retries
        ):
            time.sleep(
                _retry_delay_seconds(
                    retry_number=retry_number,
                    base_delay_seconds=retry_base_delay_seconds,
                    max_delay_seconds=retry_max_delay_seconds,
                    response=response,
                )
            )
            continue

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            raise RuntimeError(
                "HTTP error occurred while requesting subway data: "
                f"{error.response.status_code} - {error.response.text}"
            ) from error
        break

    payload: Any = response.json()
    if not isinstance(payload, list):
        raise RuntimeError("Subway API response must be a JSON array")

    return [SubwaySourceRecord.model_validate(record) for record in payload]


def _retry_delay_seconds(
    *,
    retry_number: int,
    base_delay_seconds: float,
    max_delay_seconds: float,
    response: httpx.Response | None = None,
) -> float:
    if response is not None:
        retry_after = response.headers.get("Retry-After")
        if retry_after is not None:
            try:
                delay = float(retry_after)
            except ValueError:
                try:
                    retry_at = parsedate_to_datetime(retry_after)
                    if retry_at.tzinfo is None:
                        retry_at = retry_at.replace(tzinfo=UTC)
                    delay = (retry_at - datetime.now(UTC)).total_seconds()
                except (TypeError, ValueError, OverflowError):
                    delay = -1
            if delay >= 0:
                return min(delay, max_delay_seconds)

    exponential_delay = base_delay_seconds * (2**retry_number)
    return min(exponential_delay, max_delay_seconds)


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
    max_retries: int = SOCRATA_DEFAULT_MAX_RETRIES,
    retry_base_delay_seconds: float = (
        SOCRATA_DEFAULT_RETRY_BASE_DELAY_SECONDS
    ),
    retry_max_delay_seconds: float = SOCRATA_DEFAULT_RETRY_MAX_DELAY_SECONDS,
) -> Iterator[SubwaySourceRecord]:
    url = _build_dataset_url(base_url, resource_id, response_format)
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be greater than 0")
    if app_token is not None:
        app_token = app_token.strip()
        if not app_token:
            raise ValueError("app_token must not be blank")
    if isinstance(max_retries, bool) or not isinstance(max_retries, int):
        raise ValueError("max_retries must be an integer")
    if max_retries < 0:
        raise ValueError("max_retries must be greater than or equal to 0")
    if (
        isinstance(retry_base_delay_seconds, bool)
        or not isinstance(retry_base_delay_seconds, int | float)
        or retry_base_delay_seconds < 0
    ):
        raise ValueError(
            "retry_base_delay_seconds must be a non-negative number"
        )
    if (
        isinstance(retry_max_delay_seconds, bool)
        or not isinstance(retry_max_delay_seconds, int | float)
        or retry_max_delay_seconds < 0
    ):
        raise ValueError(
            "retry_max_delay_seconds must be a non-negative number"
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
            max_retries,
            float(retry_base_delay_seconds),
            float(retry_max_delay_seconds),
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
    max_retries: int = SOCRATA_DEFAULT_MAX_RETRIES,
    retry_base_delay_seconds: float = (
        SOCRATA_DEFAULT_RETRY_BASE_DELAY_SECONDS
    ),
    retry_max_delay_seconds: float = SOCRATA_DEFAULT_RETRY_MAX_DELAY_SECONDS,
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
