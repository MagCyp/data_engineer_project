from typing import Any

import pytest

from weather_pipeline.validation.models import CityParams


@pytest.fixture
def city_params() -> CityParams:
    return CityParams(name="Berlin", latitude=52.52, longitude=13.405)


@pytest.fixture
def hourly_weather_payload() -> dict[str, Any]:
    return {
        "latitude": 41.875,
        "longitude": 12.5,
        "generationtime_ms": 0.23,
        "utc_offset_seconds": 0,
        "timezone": "GMT",
        "timezone_abbreviation": "GMT",
        "elevation": 58.0,
        "hourly_units": {
            "time": "iso8601",
            "temperature_2m": "\N{DEGREE SIGN}C",
            "rain": "mm",
            "wind_speed_10m": "km/h",
            "precipitation": "mm",
            "relative_humidity_2m": "%",
        },
        "hourly": {
            "time": ["2026-10-06T00:00", "2026-10-06T01:00"],
            "temperature_2m": [20.2, 19.7],
            "rain": [0.1, 0.0],
            "wind_speed_10m": [1.4, 1.5],
            "precipitation": [0.1, 0.0],
            "relative_humidity_2m": [71, 73],
        },
    }
