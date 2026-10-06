from collections.abc import Callable
from typing import Any
from unittest.mock import Mock

import httpx
import pytest

from weather_pipeline.ingestion.client import get_weather_data
from weather_pipeline.validation.models import CityParams, WeatherResponse


def make_response(
    status_code: int,
    *,
    json: dict[str, Any] | None = None,
    text: str | None = None,
) -> httpx.Response:
    request = httpx.Request("GET", "https://api.open-meteo.com/v1/forecast")
    return httpx.Response(
        status_code,
        json=json,
        text=text,
        request=request,
    )


def test_get_weather_data_sends_request_and_validates_response(
    monkeypatch: pytest.MonkeyPatch,
    city_params: CityParams,
    weather_payload: dict[str, Any],
) -> None:
    captured_request: dict[str, Any] = {}
    expected_weather = Mock(spec=WeatherResponse)
    validate_response = Mock(return_value=expected_weather)

    def fake_get(
        url: str,
        *,
        params: dict[str, object],
        timeout: int,
    ) -> httpx.Response:
        captured_request.update(url=url, params=params, timeout=timeout)
        return make_response(200, json=weather_payload)

    monkeypatch.setattr(httpx, "get", fake_get)
    monkeypatch.setattr(WeatherResponse, "model_validate", validate_response)

    result = get_weather_data(
        city_params=city_params,
        base_url="https://api.open-meteo.com/v1/forecast",
        timeout_seconds=30,
    )

    assert result is expected_weather
    assert captured_request == {
        "url": "https://api.open-meteo.com/v1/forecast",
        "params": {
            "latitude": 52.52,
            "longitude": 13.405,
            "current_weather": True,
        },
        "timeout": 30,
    }
    validate_response.assert_called_once_with(weather_payload)


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
    request = httpx.Request("GET", "https://api.open-meteo.com/v1/forecast")

    def fake_get(*args: object, **kwargs: object) -> httpx.Response:
        raise exception_factory(request)

    monkeypatch.setattr(httpx, "get", fake_get)

    with pytest.raises(RuntimeError, match=expected_message) as exc_info:
        get_weather_data(city_params, "https://example.com", 30)

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
        match="HTTP error occurred: 503 - Service unavailable",
    ) as exc_info:
        get_weather_data(city_params, "https://example.com", 30)

    assert isinstance(exc_info.value.__cause__, httpx.HTTPStatusError)
