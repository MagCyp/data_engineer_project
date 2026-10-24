import re
from datetime import date, datetime
from typing import Any

from common.http import RetryPolicy, get_with_retry

SOCRATA_RESOURCE_ID_PATTERN = re.compile(r"^[a-z0-9]{4}-[a-z0-9]{4}$")
SOCRATA_FIELD_PATTERN = re.compile(r"^[a-z_][a-z0-9_]*$")


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


def get_latest_socrata_date(
    resource_id: str,
    base_url: str,
    timeout_seconds: int,
    *,
    timestamp_field: str,
    max_retries: int,
    retry_base_delay_seconds: float,
    retry_max_delay_seconds: float,
    response_format: str = "json",
    app_token: str | None = None,
) -> date | None:
    """Return the date of the newest record in a Socrata dataset."""
    url = _dataset_url(base_url, resource_id, response_format)
    normalized_field = timestamp_field.strip().casefold()
    if SOCRATA_FIELD_PATTERN.fullmatch(normalized_field) is None:
        raise ValueError("timestamp_field must be a valid Socrata field name")
    if app_token is not None:
        app_token = app_token.strip()
        if not app_token:
            raise ValueError("app_token must not be blank")

    retry_policy = RetryPolicy(
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

    response = get_with_retry(
        url,
        params=params,
        headers=headers,
        timeout_seconds=timeout_seconds,
        retry_policy=retry_policy,
        request_name="Socrata data",
    )

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
