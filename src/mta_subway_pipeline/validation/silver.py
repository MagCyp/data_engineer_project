import polars as pl

from common.validation import (
    require_dataframe_schema,
    require_unique_columns,
    require_valid_rows,
)

from .models import (
    SUBWAY_GRAIN_COLUMNS,
    SUBWAY_LOCAL_TIMEZONE,
    SUBWAY_SILVER_SCHEMA,
)
from .rules import valid_subway_values


def validate_silver_subway(dataframe: pl.DataFrame) -> pl.DataFrame:
    """Validate normalized Silver subway observations and return unchanged."""
    require_dataframe_schema(
        dataframe,
        SUBWAY_SILVER_SCHEMA,
        name="Silver subway",
    )
    valid_row = (
        pl.col("observed_at_local").is_not_null()
        & pl.col("observed_at_utc").is_not_null()
        & (pl.col("timezone") == SUBWAY_LOCAL_TIMEZONE)
        & valid_subway_values()
        & pl.col("ingested_at").is_not_null()
    )
    require_valid_rows(dataframe, valid_row, name="Silver subway")
    require_unique_columns(
        dataframe,
        SUBWAY_GRAIN_COLUMNS,
        message="Silver subway data contains duplicate grain values",
    )

    return dataframe
