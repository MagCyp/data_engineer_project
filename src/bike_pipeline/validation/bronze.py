import polars as pl

from common.validation import (
    require_dataframe_schema,
    require_unique_columns,
    require_valid_rows,
)

from .models import BIKE_ALLOWED_STATUSES, BIKE_BRONZE_SCHEMA


def validate_bronze_bike(dataframe: pl.DataFrame) -> pl.DataFrame:
    """Validate parsed bike source records and return them unchanged."""
    require_dataframe_schema(dataframe, BIKE_BRONZE_SCHEMA, name="Bronze bike")

    valid_row = (
        (pl.col("countid") > 0)
        & (pl.col("id") > 0)
        & pl.col("date").is_not_null()
        & (pl.col("counts") >= 0)
        & pl.col("status").is_in(list(BIKE_ALLOWED_STATUSES))
        & pl.col("ingested_at").is_not_null()
    )
    require_valid_rows(dataframe, valid_row, name="Bronze bike")
    require_unique_columns(
        dataframe,
        "countid",
        message="Bronze bike data contains duplicate countid values",
    )

    return dataframe
