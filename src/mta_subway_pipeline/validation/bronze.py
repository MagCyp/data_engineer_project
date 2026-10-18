import polars as pl

from common.validation import require_dataframe_schema, require_valid_rows

from .models import SUBWAY_BRONZE_SCHEMA
from .rules import valid_subway_values


def validate_bronze_subway(dataframe: pl.DataFrame) -> pl.DataFrame:
    """Validate parsed subway source records and return them unchanged."""
    require_dataframe_schema(
        dataframe,
        SUBWAY_BRONZE_SCHEMA,
        name="Bronze subway",
    )
    valid_row = (
        pl.col("transit_timestamp").is_not_null()
        & (pl.col("transit_timestamp").dt.minute() == 0)
        & (pl.col("transit_timestamp").dt.second() == 0)
        & (pl.col("transit_timestamp").dt.microsecond() == 0)
        & valid_subway_values()
        & pl.col("ingested_at").is_not_null()
    )
    require_valid_rows(dataframe, valid_row, name="Bronze subway")

    return dataframe
