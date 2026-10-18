from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import polars as pl

from settings.config import get_storage_path
from storage.files import models_to_dataframe
from weather_pipeline.validation.models import (
    WEATHER_BRONZE_SCHEMA,
    WeatherObservation,
)

WEATHER_OBSERVATIONS_FILENAME = "weather_observations.parquet"
WEATHER_PIPELINE_NAME = "weather"


def _location_partition_value(location: str) -> str:
    normalized_location = "_".join(location.strip().casefold().split())
    partition_value = "".join(
        character if character.isalnum() or character in {"-", "_"} else "_"
        for character in normalized_location
    )
    partition_value = "_".join(filter(None, partition_value.split("_")))

    if not partition_value:
        raise ValueError("location must not be empty")

    return partition_value


def get_weather_observations_path(
    config: Mapping[str, Any],
    *,
    location: str,
    year: int,
    month: int,
    storage_key: str = "bronze_path",
) -> Path:
    """Return the configured year/month/location weather path."""
    storage_path = get_storage_path(
        config,
        storage_key=storage_key,
        pipeline_name=WEATHER_PIPELINE_NAME,
        year=year,
        month=month,
    )
    location_partition = _location_partition_value(location)
    return (
        storage_path
        / f"location={location_partition}"
        / WEATHER_OBSERVATIONS_FILENAME
    )


def weather_observations_to_dataframe(
    observations: Sequence[WeatherObservation],
) -> pl.DataFrame:
    """Convert weather observations into a Polars DataFrame."""
    return models_to_dataframe(
        observations,
        schema=WEATHER_BRONZE_SCHEMA,
    )
