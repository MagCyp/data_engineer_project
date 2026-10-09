from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import polars as pl

from settings.config import get_storage_path
from storage.dataframes import models_to_dataframe
from weather_pipeline.validation.models import WeatherObservation

WEATHER_OBSERVATIONS_FILENAME = "weather_observations.parquet"
WEATHER_OBSERVATION_SCHEMA = {
    "location": pl.String,
    "timezone": pl.String,
    "time": pl.Datetime(time_unit="us"),
    "temperature_2m": pl.Float64,
    "rain": pl.Float64,
    "wind_speed_10m": pl.Float64,
    "precipitation": pl.Float64,
    "relative_humidity_2m": pl.Int64,
    "ingested_at": pl.Datetime(time_unit="us", time_zone="UTC"),
}


def get_weather_observations_path(
    config: Mapping[str, Any],
    *,
    storage_key: str = "bronze_path",
) -> Path:
    """Return the configured path for weather observations."""
    return get_storage_path(config, storage_key) / WEATHER_OBSERVATIONS_FILENAME


def weather_observations_to_dataframe(
    observations: Sequence[WeatherObservation],
) -> pl.DataFrame:
    """Convert weather observations into a Polars DataFrame."""
    return models_to_dataframe(
        observations,
        schema=WEATHER_OBSERVATION_SCHEMA,
    )
