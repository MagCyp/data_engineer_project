from datetime import UTC, datetime

from weather_pipeline.validation.models import (
    HourlyWeatherResponse,
    WeatherObservation,
)


def transform_weather_response(
    data: HourlyWeatherResponse,
    location: str,
) -> list[WeatherObservation]:
    """Transform parallel hourly series into individual observations."""
    hourly = data.hourly
    ingested_at = datetime.now(UTC)

    return [
        WeatherObservation(
            location=location,
            timezone=data.timezone,
            time=time,
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
