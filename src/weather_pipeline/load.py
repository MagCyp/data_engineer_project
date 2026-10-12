from pathlib import Path

import polars as pl

from storage.database import get_engine, upsert_dataframe, weather_observations
from storage.files import load_df
from weather_pipeline.validation import validate_silver_weather

SILVER_WEATHER_SCHEMA = pl.Schema(
    {
        "location": pl.String,
        "timezone": pl.String,
        "observed_at_utc": pl.Datetime(time_unit="us", time_zone="UTC"),
        "temperature_c": pl.Float64,
        "relative_humidity_pct": pl.Int64,
        "precipitation_mm": pl.Float64,
        "rain_mm": pl.Float64,
        "wind_speed_kmh": pl.Float64,
        "ingested_at": pl.Datetime(time_unit="us", time_zone="UTC"),
    }
)


def load_weather(file_path: str | Path) -> int:
    """Validate a Silver weather Parquet file and upsert it into PostgreSQL."""
    dataframe = load_df(file_path, schema=SILVER_WEATHER_SCHEMA)
    validated_weather = validate_silver_weather(dataframe)

    engine = get_engine()
    try:
        with engine.begin() as connection:
            return upsert_dataframe(
                validated_weather,
                connection,
                weather_observations,
            )
    finally:
        engine.dispose()
