from datetime import UTC, datetime
from pathlib import Path

import polars as pl

from storage.weather import (
    WEATHER_OBSERVATION_SCHEMA,
    get_weather_observations_path,
    weather_observations_to_dataframe,
)
from weather_pipeline.validation.models import WeatherObservation


def test_weather_observations_to_dataframe() -> None:
    ingested_at = datetime(2026, 10, 7, 12, 0, tzinfo=UTC)
    observations = [
        WeatherObservation(
            location="New York",
            timezone="GMT",
            time=datetime(2025, 1, 1, 10, 0),
            temperature_2m=3.2,
            rain=0.0,
            wind_speed_10m=8.1,
            precipitation=0.0,
            relative_humidity_2m=72,
            ingested_at=ingested_at,
        )
    ]

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
    config = {"storage": {"bronze_path": str(tmp_path / "bronze")}}

    result = get_weather_observations_path(config)

    assert result == tmp_path / "bronze" / "weather_observations.parquet"
