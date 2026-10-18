import polars as pl

from common.validation import (
    finite_non_negative_numbers,
    non_empty_strings,
    require_dataframe_schema,
    require_valid_rows,
)

from .models import WEATHER_SILVER_SCHEMA


def validate_silver_weather(dataframe: pl.DataFrame) -> pl.DataFrame:
    """Validate silver weather observations and return them unchanged."""
    require_dataframe_schema(
        dataframe,
        WEATHER_SILVER_SCHEMA,
        name="Silver weather",
    )

    valid_row = (
        non_empty_strings(("location", "timezone"))
        & pl.col("observed_at_utc").is_not_null()
        & pl.col("temperature_c").is_not_null()
        & pl.col("temperature_c").is_finite()
        & pl.col("relative_humidity_pct").is_between(0, 100)
        & finite_non_negative_numbers(
            ("precipitation_mm", "rain_mm", "wind_speed_kmh")
        )
        & pl.col("ingested_at").is_not_null()
    )
    require_valid_rows(dataframe, valid_row, name="Silver weather")

    return dataframe
