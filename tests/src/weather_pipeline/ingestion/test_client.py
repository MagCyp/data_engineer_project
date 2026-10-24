from collections.abc import Callable
from datetime import date
from typing import Any
from unittest.mock import Mock

import httpx
import pytest

from common import http as http_client
from weather_pipeline.ingestion.client import get_weather_data
from weather_pipeline.validation.models import CityParams, HourlyWeatherResponse


def make_response(
    status_code: int,
    *,
    json: dict[str, Any] | None = None,
    text: str | None = None,
) -> httpx.Response:
    request = httpx.Request(
        "GET",
        "https://archive-api.open-meteo.com/v1/archive",
    )
    return httpx.Response(
        status_code,
        json=json,
        text=text,
        request=request,
    )


def test_get_weather_data_requests_historical_hourly_weather(
    monkeypatch: pytest.MonkeyPatch,
    city_params: CityParams,
    hourly_weather_payload: dict[str, Any],
) -> None:
    captured_request: dict[str, Any] = {}
    expected_weather = Mock(spec=HourlyWeatherResponse)
    validate_response = Mock(return_value=expected_weather)

    def fake_get(
        url: str,
        *,
        params: dict[str, object],
        headers: dict[str, str] | None,
        timeout: int,
    ) -> httpx.Response:
        assert headers is None
        captured_request.update(url=url, params=params, timeout=timeout)
        return make_response(200, json=hourly_weather_payload)

    monkeypatch.setattr(httpx, "get", fake_get)
    monkeypatch.setattr(HourlyWeatherResponse, "model_validate", validate_response)

    result = get_weather_data(
        city_params=city_params,
        base_url="https://archive-api.open-meteo.com/v1/archive",
        timeout_seconds=30,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 2),
        max_retries=3,
        retry_base_delay_seconds=1,
        retry_max_delay_seconds=60,
    )

    assert result is expected_weather
    assert captured_request == {
        "url": "https://archive-api.open-meteo.com/v1/archive",
        "params": {
            "latitude": 52.52,
            "longitude": 13.405,
            "start_date": "2024-01-01",
            "end_date": "2024-01-02",
            "hourly": (
                "temperature_2m,rain,wind_speed_10m,precipitation,"
                "relative_humidity_2m"
            ),
            "timezone": "GMT",
        },
        "timeout": 30,
    }
    validate_response.assert_called_once_with(hourly_weather_payload)


def test_get_weather_data_rejects_invalid_date_range(
    monkeypatch: pytest.MonkeyPatch,
    city_params: CityParams,
) -> None:
    http_get = Mock()
    monkeypatch.setattr(httpx, "get", http_get)

    with pytest.raises(
        ValueError,
        match="start_date must be less than or equal to end_date",
    ):
        get_weather_data(
            city_params,
            "https://archive-api.open-meteo.com/v1/archive",
            30,
            start_date=date(2024, 1, 2),
            end_date=date(2024, 1, 1),
            max_retries=3,
            retry_base_delay_seconds=1,
            retry_max_delay_seconds=60,
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
            "An error occurred while requesting weather data: connection refused",
        ),
        (
            lambda request: httpx.ReadTimeout(
                "request timed out",
                request=request,
            ),
            "An error occurred while requesting weather data: request timed out",
        ),
    ],
)
def test_get_weather_data_wraps_request_errors(
    monkeypatch: pytest.MonkeyPatch,
    city_params: CityParams,
    exception_factory: Callable[[httpx.Request], httpx.RequestError],
    expected_message: str,
) -> None:
    request = httpx.Request(
        "GET",
        "https://archive-api.open-meteo.com/v1/archive",
    )

    def fake_get(*args: object, **kwargs: object) -> httpx.Response:
        raise exception_factory(request)

    monkeypatch.setattr(httpx, "get", fake_get)

    with pytest.raises(RuntimeError, match=expected_message) as exc_info:
        get_weather_data(
            city_params,
            "https://archive-api.open-meteo.com/v1/archive",
            30,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 2),
            max_retries=0,
            retry_base_delay_seconds=1,
            retry_max_delay_seconds=60,
        )

    assert isinstance(exc_info.value.__cause__, httpx.RequestError)


def test_get_weather_data_wraps_http_status_error(
    monkeypatch: pytest.MonkeyPatch,
    city_params: CityParams,
) -> None:
    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: make_response(503, text="Service unavailable"),
    )

    with pytest.raises(
        RuntimeError,
        match=(
            "HTTP error occurred while requesting weather data: "
            "503 - Service unavailable"
        ),
    ) as exc_info:
        get_weather_data(
            city_params,
            "https://archive-api.open-meteo.com/v1/archive",
            30,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 2),
            max_retries=0,
            retry_base_delay_seconds=1,
            retry_max_delay_seconds=60,
        )

    assert isinstance(exc_info.value.__cause__, httpx.HTTPStatusError)


def test_get_weather_data_recovers_from_temporary_api_failure(
    monkeypatch: pytest.MonkeyPatch,
    city_params: CityParams,
    hourly_weather_payload: dict[str, Any],
) -> None:
    http_get = Mock(
        side_effect=[
            make_response(503, text="temporarily unavailable"),
            make_response(200, json=hourly_weather_payload),
        ]
    )
    sleep = Mock()
    monkeypatch.setattr(httpx, "get", http_get)
    monkeypatch.setattr(http_client.time, "sleep", sleep)

    result = get_weather_data(
        city_params,
        "https://archive-api.open-meteo.com/v1/archive",
        30,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 2),
        max_retries=1,
        retry_base_delay_seconds=0.5,
        retry_max_delay_seconds=60,
    )

    assert isinstance(result, HourlyWeatherResponse)
    assert http_get.call_count == 2
    sleep.assert_called_once_with(0.5)


def test_get_weather_data_fails_after_api_retries_are_exhausted(
    monkeypatch: pytest.MonkeyPatch,
    city_params: CityParams,
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
    monkeypatch.setattr(http_client.time, "sleep", sleep)

    with pytest.raises(RuntimeError, match="503 - unavailable after retries"):
        get_weather_data(
            city_params,
            "https://archive-api.open-meteo.com/v1/archive",
            30,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 2),
            max_retries=2,
            retry_base_delay_seconds=1,
            retry_max_delay_seconds=10,
        )

    assert http_get.call_count == 3
    assert [call.args[0] for call in sleep.call_args_list] == [1, 2]
