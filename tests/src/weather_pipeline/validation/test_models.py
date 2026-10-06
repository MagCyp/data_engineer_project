from datetime import datetime
from typing import Any

import pytest
from pydantic import ValidationError

from weather_pipeline.validation.models import CityParams, WeatherResponse


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


def test_weather_response_parses_nested_models_and_datetime(
    weather_payload: dict[str, Any],
) -> None:
    weather = WeatherResponse.model_validate(weather_payload)

    assert weather.latitude == 52.52
    assert weather.current_weather.time == datetime(2026, 10, 5, 12, 0)
    assert weather.current_weather.temperature == 14.2
    assert weather.current_weather.is_day == 1
    assert weather.current_weather_units.temperature == "\N{DEGREE SIGN}C"


def test_weather_response_rejects_invalid_day_indicator(
    weather_payload: dict[str, Any],
) -> None:
    weather_payload["current_weather"]["is_day"] = 2

    with pytest.raises(ValidationError) as exc_info:
        WeatherResponse.model_validate(weather_payload)

    assert exc_info.value.errors()[0]["loc"] == ("current_weather", "is_day")


def test_weather_response_requires_current_weather_fields(
    weather_payload: dict[str, Any],
) -> None:
    del weather_payload["current_weather"]["temperature"]

    with pytest.raises(ValidationError) as exc_info:
        WeatherResponse.model_validate(weather_payload)

    assert exc_info.value.errors()[0]["loc"] == (
        "current_weather",
        "temperature",
    )
