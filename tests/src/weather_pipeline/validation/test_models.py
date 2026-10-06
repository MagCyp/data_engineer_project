from datetime import datetime
from typing import Any

import pytest
from pydantic import ValidationError

from weather_pipeline.validation.models import CityParams, HourlyWeatherResponse


def test_city_params_matches_project_config_shape() -> None:
    city = CityParams.model_validate(
        {
            "name": " Berlin ",
            "latitude": 52.52,
            "longitude": 13.405,
        }
    )

    assert city.name == "Berlin"
    assert city.latitude == 52.52
    assert city.longitude == 13.405


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("latitude", -90.01),
        ("latitude", 90.01),
        ("longitude", -180.01),
        ("longitude", 180.01),
    ],
)
def test_city_params_rejects_coordinates_outside_valid_range(
    field: str,
    value: float,
) -> None:
    payload = {
        "name": "Berlin",
        "latitude": 52.52,
        "longitude": 13.405,
    }
    payload[field] = value

    with pytest.raises(ValidationError) as exc_info:
        CityParams.model_validate(payload)

    assert exc_info.value.errors()[0]["loc"] == (field,)


def test_city_params_rejects_blank_name() -> None:
    with pytest.raises(ValidationError) as exc_info:
        CityParams(name="   ", latitude=52.52, longitude=13.405)

    assert exc_info.value.errors()[0]["loc"] == ("name",)


def test_hourly_weather_response_parses_typed_series(
    hourly_weather_payload: dict[str, Any],
) -> None:
    weather = HourlyWeatherResponse.model_validate(hourly_weather_payload)

    assert weather.latitude == 41.875
    assert weather.hourly.time == [
        datetime(2026, 10, 6, 0, 0),
        datetime(2026, 10, 6, 1, 0),
    ]
    assert weather.hourly.temperature_2m == [20.2, 19.7]
    assert weather.hourly.relative_humidity_2m == [71, 73]
    assert weather.hourly_units.wind_speed_10m == "km/h"


def test_hourly_weather_response_requires_equal_series_lengths(
    hourly_weather_payload: dict[str, Any],
) -> None:
    hourly_weather_payload["hourly"]["rain"].pop()

    with pytest.raises(
        ValidationError,
        match="All hourly weather series must have equal lengths",
    ):
        HourlyWeatherResponse.model_validate(hourly_weather_payload)


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("relative_humidity_2m", -1),
        ("rain", -0.1),
        ("wind_speed_10m", -0.1),
    ],
)
def test_hourly_weather_response_rejects_invalid_measurements(
    hourly_weather_payload: dict[str, Any],
    field: str,
    invalid_value: int | float,
) -> None:
    hourly_weather_payload["hourly"][field][0] = invalid_value

    with pytest.raises(ValidationError):
        HourlyWeatherResponse.model_validate(hourly_weather_payload)
