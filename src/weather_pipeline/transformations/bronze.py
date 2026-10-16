from datetime import UTC, datetime

from common.validation import normalize_utc_datetime
from weather_pipeline.validation.models import (
    HourlyWeatherResponse,
    WeatherObservation,
)


def _to_utc(value: datetime, source_timezone: str) -> datetime:
    if value.tzinfo is not None and value.utcoffset() is not None:
        return normalize_utc_datetime(value)

    if source_timezone not in {"GMT", "UTC"}:
        raise ValueError(
            "Naive weather timestamps can only be normalized from GMT or UTC"
        )

    return value.replace(tzinfo=UTC)


def transform_response_to_bronze(
    data: HourlyWeatherResponse,
    location: str,
) -> list[WeatherObservation]:
    """Transform an hourly API response into bronze weather observations."""
    hourly = data.hourly
    ingested_at = datetime.now(UTC)

    return [
        WeatherObservation(
            location=location,
            timezone=data.timezone,
            time=_to_utc(time, data.timezone),
            temperature_2m=temperature,
            rain=rain,
            wind_speed_10m=wind_speed,
            precipitation=precipitation,
            relative_humidity_2m=humidity,
            ingested_at=ingested_at,
        )
        for time, temperature, rain, wind_speed, precipitation, humidity in zip(
            hourly.time,
            hourly.temperature_2m,
            hourly.rain,
            hourly.wind_speed_10m,
            hourly.precipitation,
            hourly.relative_humidity_2m,
            strict=True,
        )
    ]
