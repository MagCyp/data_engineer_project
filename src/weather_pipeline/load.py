from pathlib import Path

from storage.database import load_parquet_to_table, weather_observations
from weather_pipeline.validation import (
    WEATHER_SILVER_SCHEMA,
    validate_silver_weather,
)


def load_weather(file_path: str | Path) -> int:
    """Validate a Silver weather Parquet file and upsert it into PostgreSQL."""
    return load_parquet_to_table(
        file_path,
        schema=WEATHER_SILVER_SCHEMA,
        validator=validate_silver_weather,
        table=weather_observations,
    )
