import time
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

import httpx

HTTP_RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})


@dataclass(frozen=True, slots=True)
class RetryPolicy:
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


def get_with_retry(
    url: str,
    *,
    params: Mapping[str, str | int | float],
    headers: Mapping[str, str] | None,
    timeout_seconds: int,
    retry_policy: RetryPolicy,
    request_name: str,
) -> httpx.Response:
    """Send an HTTP GET and retry temporary transport and server failures."""
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be greater than 0")

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
                f"An error occurred while requesting {request_name}: {error}"
            ) from error

        if (
            response.status_code in HTTP_RETRYABLE_STATUS_CODES
            and retry_number < retry_policy.max_retries
        ):
            time.sleep(retry_policy.delay(retry_number, response))
            continue

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            raise RuntimeError(
                f"HTTP error occurred while requesting {request_name}: "
                f"{error.response.status_code} - {error.response.text}"
            ) from error
        return response

    raise RuntimeError(f"Retry loop for {request_name} ended unexpectedly")


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
