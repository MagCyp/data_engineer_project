from typing import Any
from unittest.mock import Mock

import pytest

from weather_pipeline.ingestion import service
from weather_pipeline.validation.models import CityParams, WeatherResponse


@pytest.fixture
def config() -> dict[str, Any]:
    return {
        "api": {
            "base_url": "https://api.open-meteo.com/v1/forecast",
            "timeout_seconds": 30,
        },
        "locations": [
            {"name": "Rome", "latitude": 41.9028, "longitude": 12.4964},
            {"name": "Berlin", "latitude": 52.52, "longitude": 13.405},
        ],
    }


def test_get_location_by_name_builds_city_params(
    config: dict[str, Any],
) -> None:
    result = service.get_location_by_name("Berlin", config["locations"])

    assert result == CityParams(
        name="Berlin",
        latitude=52.52,
        longitude=13.405,
    )


def test_get_location_by_name_accepts_prevalidated_models(
    city_params: CityParams,
) -> None:
    result = service.get_location_by_name("Berlin", [city_params])

    assert result is city_params


def test_get_location_by_name_raises_for_unknown_city(
    config: dict[str, Any],
) -> None:
    with pytest.raises(
        ValueError,
        match="City 'Paris' not found in the configured locations",
    ):
        service.get_location_by_name("Paris", config["locations"])


def test_fetch_weather_for_location_delegates_to_client(
    monkeypatch: pytest.MonkeyPatch,
    config: dict[str, Any],
    city_params: CityParams,
) -> None:
    expected_weather = Mock(spec=WeatherResponse)
    find_location = Mock(return_value=city_params)
    fetch_weather = Mock(return_value=expected_weather)
    monkeypatch.setattr(service, "get_location_by_name", find_location)
    monkeypatch.setattr(service, "get_weather_data", fetch_weather)

    result = service.fetch_weather_for_location(config, "Berlin")

    assert result is expected_weather
    find_location.assert_called_once_with("Berlin", config["locations"])
    fetch_weather.assert_called_once_with(
        city_params=city_params,
        base_url="https://api.open-meteo.com/v1/forecast",
        timeout_seconds=30,
    )
