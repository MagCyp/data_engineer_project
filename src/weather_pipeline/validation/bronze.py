import polars as pl

from common.validation import (
    finite_non_negative_numbers,
    non_empty_strings,
    require_dataframe_schema,
    require_valid_rows,
)

from .models import WEATHER_BRONZE_SCHEMA


def validate_bronze_weather(dataframe: pl.DataFrame) -> pl.DataFrame:
    """Validate bronze weather observations and return them unchanged."""
    require_dataframe_schema(
        dataframe,
        WEATHER_BRONZE_SCHEMA,
        name="Bronze weather",
    )

    valid_row = (
        non_empty_strings(("location", "timezone"))
        & pl.col("time").is_not_null()
        & pl.col("temperature_2m").is_not_null()
        & pl.col("temperature_2m").is_finite()
        & pl.col("relative_humidity_2m").is_between(0, 100)
        & finite_non_negative_numbers(
            ("precipitation", "rain", "wind_speed_10m")
        )
        & pl.col("ingested_at").is_not_null()
    )
    require_valid_rows(dataframe, valid_row, name="Bronze weather")

    return dataframe
