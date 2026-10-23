from datetime import date
from typing import Any

import httpx
import pytest

from active_mobility_pipeline.ingestion.client import (
    get_active_mobility_sensors,
    iter_active_mobility_counts,
)


def response(payload: Any) -> httpx.Response:
    return httpx.Response(
        200,
        json=payload,
        request=httpx.Request(
            "GET",
            "https://data.cityofnewyork.us/resource/ct66-47at.json",
        ),
    )


def count_payload(timestamp: str) -> dict[str, object]:
    return {
        "sensor_id": "100",
        "travelmode": "bike",
        "direction": "in",
        "flowid": "101",
        "flowname": "Bike IN",
        "timestamp": timestamp,
        "granularity": "PT15M",
        "counts": "18",
        "status": "raw",
    }


def sensor_payload() -> dict[str, object]:
    return {
        "id": "100",
        "name": "Shared Counter",
        "lat": "40.7",
        "lon": "-73.9",
        "firstdata": "2022-09-02T11:15:00.000",
        "lastdata": "2026-10-22T01:15:00.000",
        "granularity": "PT15M",
        "travelmodes": "bike, pedestrian",
        "directional": True,
        "hastimestampeddata": False,
        "hasweather": True,
        "domain_name": "New York City DOT",
    }


def test_count_client_pages_and_filters_requested_dates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pages = [
        [
            count_payload("2025-01-15T08:00:00.000"),
            count_payload("2025-01-15T08:15:00.000"),
        ],
        [count_payload("2025-01-15T08:30:00.000")],
    ]
    captured_params: list[dict[str, str | int]] = []

    def fake_get(
        url: str,
        *,
        params: dict[str, str | int],
        headers: dict[str, str] | None,
        timeout: int,
    ) -> httpx.Response:
        assert url.endswith("/ct66-47at.json")
        assert headers is None
        assert timeout == 60
        captured_params.append(params)
        return response(pages.pop(0))

    monkeypatch.setattr(httpx, "get", fake_get)
    records = list(
        iter_active_mobility_counts(
            "ct66-47at",
            "https://data.cityofnewyork.us/resource",
            60,
            start_date=date(2025, 1, 15),
            end_date=date(2025, 1, 15),
            page_size=2,
        )
    )

    assert len(records) == 3
    assert [params["$offset"] for params in captured_params] == [0, 2]
    assert captured_params[0]["$where"] == (
        "timestamp >= '2025-01-15T00:00:00.000' AND "
        "timestamp < '2025-01-16T00:00:00.000'"
    )


def test_sensor_client_uses_sensor_resource(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_get(
        url: str,
        *,
        params: dict[str, str | int],
        headers: dict[str, str] | None,
        timeout: int,
    ) -> httpx.Response:
        assert url.endswith("/6up2-gnw8.json")
        assert params["$order"] == "id,counters_installationdate"
        assert headers == {"X-App-Token": "token"}
        assert timeout == 60
        return response([sensor_payload()])

    monkeypatch.setattr(httpx, "get", fake_get)
    records = get_active_mobility_sensors(
        "6up2-gnw8",
        "https://data.cityofnewyork.us/resource",
        60,
        app_token="token",
    )

    assert len(records) == 1
    assert records[0].travelmodes == "bike, pedestrian"
