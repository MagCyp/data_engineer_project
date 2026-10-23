import re
import time
from dataclasses import dataclass
from datetime import UTC, date, datetime
from email.utils import parsedate_to_datetime
from typing import Any

import httpx

SOCRATA_DEFAULT_MAX_RETRIES = 3
SOCRATA_DEFAULT_RETRY_BASE_DELAY_SECONDS = 1.0
SOCRATA_DEFAULT_RETRY_MAX_DELAY_SECONDS = 60.0
SOCRATA_RETRYABLE_STATUS_CODES = frozenset({429, 502, 503, 504})
SOCRATA_RESOURCE_ID_PATTERN = re.compile(r"^[a-z0-9]{4}-[a-z0-9]{4}$")
SOCRATA_FIELD_PATTERN = re.compile(r"^[a-z_][a-z0-9_]*$")


@dataclass(frozen=True, slots=True)
class _RetryPolicy:
    max_retries: int
    base_delay_seconds: float
    max_delay_seconds: float

    def __post_init__(self) -> None:
        if isinstance(self.max_retries, bool) or not isinstance(
            self.max_retries,
            int,
        ):
            raise ValueError("max_retries must be an integer")
        if self.max_retries < 0:
            raise ValueError("max_retries must be greater than or equal to 0")

        for name, value in (
            ("retry_base_delay_seconds", self.base_delay_seconds),
            ("retry_max_delay_seconds", self.max_delay_seconds),
        ):
            if (
                isinstance(value, bool)
                or not isinstance(value, int | float)
                or value < 0
            ):
                raise ValueError(f"{name} must be a non-negative number")

    def delay(
        self,
        retry_number: int,
        response: httpx.Response | None = None,
    ) -> float:
        retry_after = _retry_after_seconds(response)
        if retry_after is not None:
            return min(retry_after, self.max_delay_seconds)
        return min(
            self.base_delay_seconds * (2**retry_number),
            self.max_delay_seconds,
        )


def _dataset_url(
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

    return f"{normalized_base_url}/{normalized_resource_id}.json"


def _retry_after_seconds(response: httpx.Response | None) -> float | None:
    if response is None or "Retry-After" not in response.headers:
        return None

    retry_after = response.headers["Retry-After"]
    try:
        delay = float(retry_after)
    except ValueError:
        try:
            retry_at = parsedate_to_datetime(retry_after)
            if retry_at.tzinfo is None:
                retry_at = retry_at.replace(tzinfo=UTC)
            delay = (retry_at - datetime.now(UTC)).total_seconds()
        except (TypeError, ValueError, OverflowError):
            return None
    return max(delay, 0)


def get_latest_socrata_date(
    resource_id: str,
    base_url: str,
    timeout_seconds: int,
    *,
    timestamp_field: str,
    response_format: str = "json",
    app_token: str | None = None,
    max_retries: int = SOCRATA_DEFAULT_MAX_RETRIES,
    retry_base_delay_seconds: float = (
        SOCRATA_DEFAULT_RETRY_BASE_DELAY_SECONDS
    ),
    retry_max_delay_seconds: float = SOCRATA_DEFAULT_RETRY_MAX_DELAY_SECONDS,
) -> date | None:
    """Return the date of the newest record in a Socrata dataset."""
    url = _dataset_url(base_url, resource_id, response_format)
    normalized_field = timestamp_field.strip().casefold()
    if SOCRATA_FIELD_PATTERN.fullmatch(normalized_field) is None:
        raise ValueError("timestamp_field must be a valid Socrata field name")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be greater than 0")
    if app_token is not None:
        app_token = app_token.strip()
        if not app_token:
            raise ValueError("app_token must not be blank")

    retry_policy = _RetryPolicy(
        max_retries=max_retries,
        base_delay_seconds=retry_base_delay_seconds,
        max_delay_seconds=retry_max_delay_seconds,
    )
    headers = None if app_token is None else {"X-App-Token": app_token}
    params: dict[str, str | int] = {
        "$select": normalized_field,
        "$order": f"{normalized_field} DESC",
        "$limit": 1,
    }

    for retry_number in range(retry_policy.max_retries + 1):
        try:
            response = httpx.get(
                url,
                params=params,
                headers=headers,
                timeout=timeout_seconds,
            )
        except httpx.RequestError as error:
            if retry_number < retry_policy.max_retries:
                time.sleep(retry_policy.delay(retry_number))
                continue
            raise RuntimeError(
                f"An error occurred while requesting Socrata data: {error}"
            ) from error

        if (
            response.status_code in SOCRATA_RETRYABLE_STATUS_CODES
            and retry_number < retry_policy.max_retries
        ):
            time.sleep(retry_policy.delay(retry_number, response))
            continue

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            raise RuntimeError(
                "HTTP error occurred while requesting Socrata data: "
                f"{error.response.status_code} - {error.response.text}"
            ) from error
        break

    payload: Any = response.json()
    if not isinstance(payload, list) or not all(
        isinstance(item, dict) for item in payload
    ):
        raise RuntimeError("Socrata API response must be a JSON array")
    if not payload:
        return None

    timestamp = payload[0].get(normalized_field)
    if not isinstance(timestamp, str):
        raise RuntimeError(
            f"Latest Socrata record must contain {normalized_field}"
        )
    try:
        return datetime.fromisoformat(timestamp).date()
    except ValueError as error:
        raise RuntimeError(
            f"Invalid latest Socrata timestamp: {timestamp}"
        ) from error
