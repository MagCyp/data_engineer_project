from typing import Any

import pytest

from weather_pipeline.validation.models import CityParams


@pytest.fixture
def city_params() -> CityParams:
    return CityParams(name="Berlin", latitude=52.52, longitude=13.405)


@pytest.fixture
def weather_payload() -> dict[str, Any]:
    return {
        "latitude": 52.52,
        "longitude": 13.42,
        "generationtime_ms": 0.06,
        "utc_offset_seconds": 0,
        "timezone": "GMT",
        "timezone_abbreviation": "GMT",
        "elevation": 38.0,
        "current_weather_units": {
            "time": "iso8601",
            "interval": "seconds",
            "temperature": "\N{DEGREE SIGN}C",
            "windspeed": "km/h",
            "winddirection": "\N{DEGREE SIGN}",
            "is_day": "",
            "weathercode": "wmo code",
        },
        "current_weather": {
            "time": "2026-10-05T12:00",
            "interval": 900,
            "temperature": 14.2,
            "windspeed": 11.7,
            "winddirection": 245.0,
            "is_day": 1,
            "weathercode": 3,
        },
    }
