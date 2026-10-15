import polars as pl

from .models import (
    BIKE_ALLOWED_STATUSES,
    BIKE_LOCAL_TIMEZONE,
    BIKE_SILVER_SCHEMA,
)


def validate_silver_bike(dataframe: pl.DataFrame) -> pl.DataFrame:
    """Validate normalized Silver bike observations and return them unchanged."""
    missing_columns = set(BIKE_SILVER_SCHEMA.names()).difference(dataframe.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing Silver bike columns: {missing}")

    for column, expected_dtype in BIKE_SILVER_SCHEMA.items():
        if dataframe.schema[column] != expected_dtype:
            raise ValueError(
                f"Silver bike column '{column}' must use {expected_dtype}"
            )

    valid_row = (
        (pl.col("record_id") > 0)
        & (pl.col("counter_id") > 0)
        & (pl.col("timezone") == BIKE_LOCAL_TIMEZONE)
        & pl.col("observed_at_local").is_not_null()
        & pl.col("observed_at_utc").is_not_null()
        & (pl.col("bike_count") >= 0)
        & pl.col("status").is_in(list(BIKE_ALLOWED_STATUSES))
        & pl.col("ingested_at").is_not_null()
    ).fill_null(False)
    invalid_count = dataframe.select((~valid_row).sum()).item()
    if invalid_count:
        raise ValueError(
            f"Silver bike validation failed for {invalid_count} row(s)"
        )

    if dataframe["record_id"].is_duplicated().any():
        raise ValueError("Silver bike data contains duplicate record_id values")

    return dataframe
