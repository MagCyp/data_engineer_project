from collections.abc import Callable
from datetime import date
from typing import Any
from unittest.mock import Mock

import httpx
import pytest

from mta_subway_pipeline.ingestion import client
from mta_subway_pipeline.ingestion.client import get_subway_data


def make_record(timestamp: str) -> dict[str, object]:
    return {
        "transit_timestamp": timestamp,
        "transit_mode": "subway",
        "station_complex_id": "158",
        "station_complex": "86 St (C,B)",
        "borough": "Manhattan",
        "payment_method": "omny",
        "fare_class_category": "OMNY - Full Fare",
        "ridership": "451.0",
        "transfers": "26.0",
        "latitude": "40.78587",
        "longitude": "-73.96892",
        "georeference": {
            "type": "Point",
            "coordinates": [-73.96892, 40.78587],
        },
    }


def make_response(
    status_code: int,
    *,
    json: Any = None,
    text: str | None = None,
    headers: dict[str, str] | None = None,
) -> httpx.Response:
    request = httpx.Request(
        "GET",
        "https://data.ny.gov/resource/5wq4-mkjj.json",
    )
    return httpx.Response(
        status_code,
        json=json,
        text=text,
        headers=headers,
        request=request,
    )


def test_get_subway_data_requests_and_validates_all_pages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_params: list[dict[str, str | int]] = []
    pages = [
        [
            make_record("2025-01-15T08:00:00.000"),
            make_record("2025-01-15T09:00:00.000"),
        ],
        [make_record("2025-01-15T10:00:00.000")],
    ]

    def fake_get(
        url: str,
        *,
        params: dict[str, str | int],
        timeout: int,
    ) -> httpx.Response:
        assert url == "https://data.ny.gov/resource/5wq4-mkjj.json"
        assert timeout == 60
        captured_params.append(params)
        return make_response(200, json=pages.pop(0))

    monkeypatch.setattr(httpx, "get", fake_get)

    records = get_subway_data(
        resource_id="5wq4-mkjj",
        base_url="https://data.ny.gov/resource",
        timeout_seconds=60,
        start_date=date(2025, 1, 15),
        end_date=date(2025, 1, 15),
        page_size=2,
    )

    assert len(records) == 3
    assert [params["$offset"] for params in captured_params] == [0, 2]
    assert captured_params[0]["$where"] == (
        "transit_timestamp >= '2025-01-15T00:00:00.000' AND "
        "transit_timestamp < '2025-01-16T00:00:00.000'"
    )
    assert captured_params[0]["$limit"] == 2


def test_get_subway_data_rejects_invalid_date_range(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    http_get = Mock()
    monkeypatch.setattr(httpx, "get", http_get)

    with pytest.raises(
        ValueError,
        match="start_date must be before or equal to end_date",
    ):
        get_subway_data(
            resource_id="5wq4-mkjj",
            base_url="https://data.ny.gov/resource",
            timeout_seconds=60,
            start_date=date(2025, 1, 16),
            end_date=date(2025, 1, 15),
        )

    http_get.assert_not_called()


@pytest.mark.parametrize(
    ("exception_factory", "expected_message"),
    [
        (
            lambda request: httpx.ConnectError(
                "connection refused",
                request=request,
            ),
            "An error occurred while requesting subway data: connection refused",
        ),
        (
            lambda request: httpx.ReadTimeout(
                "request timed out",
                request=request,
            ),
            "An error occurred while requesting subway data: request timed out",
        ),
    ],
)
def test_get_subway_data_wraps_request_errors(
    monkeypatch: pytest.MonkeyPatch,
    exception_factory: Callable[[httpx.Request], httpx.RequestError],
    expected_message: str,
) -> None:
    request = httpx.Request(
        "GET",
        "https://data.ny.gov/resource/5wq4-mkjj.json",
    )

    def fake_get(*args: object, **kwargs: object) -> httpx.Response:
        raise exception_factory(request)

    monkeypatch.setattr(httpx, "get", fake_get)

    with pytest.raises(RuntimeError, match=expected_message) as exc_info:
        get_subway_data(
            resource_id="5wq4-mkjj",
            base_url="https://data.ny.gov/resource",
            timeout_seconds=60,
            start_date=date(2025, 1, 15),
            end_date=date(2025, 1, 15),
            max_retries=0,
        )

    assert isinstance(exc_info.value.__cause__, httpx.RequestError)


def test_get_subway_data_retries_429_using_retry_after(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    http_get = Mock(
        side_effect=[
            make_response(
                429,
                text="rate limited",
                headers={"Retry-After": "3"},
            ),
            make_response(
                200,
                json=[make_record("2025-01-15T08:00:00.000")],
            ),
        ]
    )
    sleep = Mock()
    monkeypatch.setattr(httpx, "get", http_get)
    monkeypatch.setattr(client.time, "sleep", sleep)

    records = get_subway_data(
        resource_id="5wq4-mkjj",
        base_url="https://data.ny.gov/resource",
        timeout_seconds=60,
        start_date=date(2025, 1, 15),
        end_date=date(2025, 1, 15),
        max_retries=1,
    )

    assert len(records) == 1
    assert http_get.call_count == 2
    sleep.assert_called_once_with(3.0)


def test_get_subway_data_retries_temporary_network_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = httpx.Request(
        "GET",
        "https://data.ny.gov/resource/5wq4-mkjj.json",
    )
    http_get = Mock(
        side_effect=[
            httpx.ReadTimeout("request timed out", request=request),
            make_response(200, json=[]),
        ]
    )
    sleep = Mock()
    monkeypatch.setattr(httpx, "get", http_get)
    monkeypatch.setattr(client.time, "sleep", sleep)

    records = get_subway_data(
        resource_id="5wq4-mkjj",
        base_url="https://data.ny.gov/resource",
        timeout_seconds=60,
        start_date=date(2025, 1, 15),
        end_date=date(2025, 1, 15),
        max_retries=1,
        retry_base_delay_seconds=0.5,
    )

    assert records == []
    assert http_get.call_count == 2
    sleep.assert_called_once_with(0.5)


def test_get_subway_data_raises_after_retries_are_exhausted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    http_get = Mock(
        side_effect=[
            make_response(503, text="unavailable"),
            make_response(503, text="still unavailable"),
            make_response(503, text="unavailable after retries"),
        ]
    )
    sleep = Mock()
    monkeypatch.setattr(httpx, "get", http_get)
    monkeypatch.setattr(client.time, "sleep", sleep)

    with pytest.raises(RuntimeError, match="503"):
        get_subway_data(
            resource_id="5wq4-mkjj",
            base_url="https://data.ny.gov/resource",
            timeout_seconds=60,
            start_date=date(2025, 1, 15),
            end_date=date(2025, 1, 15),
            max_retries=2,
            retry_base_delay_seconds=1,
            retry_max_delay_seconds=10,
        )

    assert http_get.call_count == 3
    assert [call.args[0] for call in sleep.call_args_list] == [1.0, 2.0]
