from datetime import date
from unittest.mock import Mock

import httpx
import pytest

from common import socrata


def make_response(
    status_code: int,
    *,
    json: object = None,
    text: str | None = None,
    headers: dict[str, str] | None = None,
) -> httpx.Response:
    return httpx.Response(
        status_code,
        json=json,
        text=text,
        headers=headers,
        request=httpx.Request(
            "GET",
            "https://data.example.org/resource/abcd-1234.json",
        ),
    )


def test_get_latest_socrata_date_queries_configured_field(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    http_get = Mock(
        return_value=make_response(
            200,
            json=[{"observed_at": "2026-10-23T05:00:00.000"}],
        )
    )
    monkeypatch.setattr(httpx, "get", http_get)

    latest_date = socrata.get_latest_socrata_date(
        resource_id="abcd-1234",
        base_url="https://data.example.org/resource/",
        timeout_seconds=60,
        timestamp_field="observed_at",
        app_token="token",
    )

    assert latest_date == date(2026, 10, 23)
    assert http_get.call_args.args == (
        "https://data.example.org/resource/abcd-1234.json",
    )
    assert http_get.call_args.kwargs["params"] == {
        "$select": "observed_at",
        "$order": "observed_at DESC",
        "$limit": 1,
    }
    assert http_get.call_args.kwargs["headers"] == {"X-App-Token": "token"}


def test_get_latest_socrata_date_returns_none_for_empty_dataset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        httpx,
        "get",
        Mock(return_value=make_response(200, json=[])),
    )

    assert socrata.get_latest_socrata_date(
        resource_id="abcd-1234",
        base_url="https://data.example.org/resource",
        timeout_seconds=60,
        timestamp_field="observed_at",
    ) is None


def test_get_latest_socrata_date_retries_rate_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    http_get = Mock(
        side_effect=[
            make_response(
                429,
                text="rate limited",
                headers={"Retry-After": "2"},
            ),
            make_response(
                200,
                json=[{"observed_at": "2026-10-23T05:00:00.000"}],
            ),
        ]
    )
    sleep = Mock()
    monkeypatch.setattr(httpx, "get", http_get)
    monkeypatch.setattr(socrata.time, "sleep", sleep)

    result = socrata.get_latest_socrata_date(
        resource_id="abcd-1234",
        base_url="https://data.example.org/resource",
        timeout_seconds=60,
        timestamp_field="observed_at",
        max_retries=1,
    )

    assert result == date(2026, 10, 23)
    assert http_get.call_count == 2
    sleep.assert_called_once_with(2.0)


def test_get_latest_socrata_date_rejects_unsafe_field() -> None:
    with pytest.raises(ValueError, match="valid Socrata field name"):
        socrata.get_latest_socrata_date(
            resource_id="abcd-1234",
            base_url="https://data.example.org/resource",
            timeout_seconds=60,
            timestamp_field="timestamp DESC LIMIT 100",
        )
