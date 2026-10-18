import polars as pl

from common.validation import (
    require_dataframe_schema,
    require_unique_columns,
    require_valid_rows,
)

from .models import (
    BIKE_ALLOWED_STATUSES,
    BIKE_LOCAL_TIMEZONE,
    BIKE_SILVER_SCHEMA,
)


def validate_silver_bike(dataframe: pl.DataFrame) -> pl.DataFrame:
    """Validate normalized Silver bike observations and return them unchanged."""
    require_dataframe_schema(dataframe, BIKE_SILVER_SCHEMA, name="Silver bike")

    valid_row = (
        (pl.col("record_id") > 0)
        & (pl.col("counter_id") > 0)
        & (pl.col("timezone") == BIKE_LOCAL_TIMEZONE)
        & pl.col("observed_at_local").is_not_null()
        & pl.col("observed_at_utc").is_not_null()
        & (pl.col("bike_count") >= 0)
        & pl.col("status").is_in(list(BIKE_ALLOWED_STATUSES))
        & pl.col("ingested_at").is_not_null()
    )
    require_valid_rows(dataframe, valid_row, name="Silver bike")
    require_unique_columns(
        dataframe,
        "record_id",
        message="Silver bike data contains duplicate record_id values",
    )

    return dataframe
