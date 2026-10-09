from datetime import UTC, datetime
from typing import Any

from weather_pipeline.transformations.observations import (
    transform_weather_response,
)
from weather_pipeline.validation.models import (
    HourlyWeatherResponse,
    WeatherObservation,
)


def test_transform_weather_response_returns_observation_models(
    hourly_weather_payload: dict[str, Any],
) -> None:
    response = HourlyWeatherResponse.model_validate(hourly_weather_payload)
    before_transform = datetime.now(UTC)

    result = transform_weather_response(response, location="New York")
    after_transform = datetime.now(UTC)

    assert len(result) == 2
    assert result[0].model_dump(exclude={"ingested_at"}) == {
        "location": "New York",
        "timezone": "GMT",
        "time": datetime(2026, 10, 6, 0, 0),
        "temperature_2m": 20.2,
        "rain": 0.1,
        "wind_speed_10m": 1.4,
        "precipitation": 0.1,
        "relative_humidity_2m": 71,
    }
    assert result[1].model_dump(exclude={"ingested_at"}) == {
        "location": "New York",
        "timezone": "GMT",
        "time": datetime(2026, 10, 6, 1, 0),
        "temperature_2m": 19.7,
        "rain": 0.0,
        "wind_speed_10m": 1.5,
        "precipitation": 0.0,
        "relative_humidity_2m": 73,
    }
    assert {
        observation.ingested_at for observation in result
    } == {result[0].ingested_at}
    assert before_transform <= result[0].ingested_at <= after_transform
    assert all(
        isinstance(item, WeatherObservation)
        for item in result
    )
