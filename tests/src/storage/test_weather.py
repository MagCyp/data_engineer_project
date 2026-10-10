from datetime import UTC, datetime
from pathlib import Path

import polars as pl

from storage.weather import (
    WEATHER_OBSERVATION_SCHEMA,
    get_weather_observations_path,
    weather_observations_to_dataframe,
)
from weather_pipeline.validation.models import WeatherObservation


def weather_observation(observed_at: datetime) -> WeatherObservation:
    return WeatherObservation(
        location="New York",
        timezone="GMT",
        time=observed_at,
        temperature_2m=3.2,
        rain=0.0,
        wind_speed_10m=8.1,
        precipitation=0.0,
        relative_humidity_2m=72,
        ingested_at=datetime(2026, 10, 7, 12, 0, tzinfo=UTC),
    )


def test_weather_observations_to_dataframe() -> None:
    observations = [weather_observation(datetime(2025, 1, 1, 10, 0))]

    result = weather_observations_to_dataframe(observations)

    assert result.to_dicts() == [observations[0].model_dump()]
    assert result.schema == pl.Schema(WEATHER_OBSERVATION_SCHEMA)


def test_weather_observations_to_dataframe_keeps_schema_when_empty() -> None:
    result = weather_observations_to_dataframe([])

    assert result.is_empty()
    assert result.schema == pl.Schema(WEATHER_OBSERVATION_SCHEMA)


def test_get_weather_observations_path_uses_configured_storage(
    tmp_path: Path,
) -> None:
    path_template = tmp_path / "bronze" / "year={year}" / "month={month}"
    config = {"storage": {"bronze_path": str(path_template)}}

    result = get_weather_observations_path(
        config,
        year=2025,
        month=1,
    )

    assert result == (
        tmp_path
        / "bronze"
        / "year=2025"
        / "month=01"
        / "weather_observations.parquet"
    )
