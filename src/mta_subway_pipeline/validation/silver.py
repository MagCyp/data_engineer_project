import polars as pl

from .models import (
    SUBWAY_GRAIN_COLUMNS,
    SUBWAY_LOCAL_TIMEZONE,
    SUBWAY_SILVER_SCHEMA,
)


def validate_silver_subway(dataframe: pl.DataFrame) -> pl.DataFrame:
    """Validate normalized Silver subway observations and return unchanged."""
    missing_columns = set(SUBWAY_SILVER_SCHEMA.names()).difference(
        dataframe.columns
    )
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing Silver subway columns: {missing}")

    for column, expected_dtype in SUBWAY_SILVER_SCHEMA.items():
        if dataframe.schema[column] != expected_dtype:
            raise ValueError(
                f"Silver subway column '{column}' must use {expected_dtype}"
            )

    non_empty_columns = (
        "transit_mode",
        "station_complex_id",
        "station_complex",
        "borough",
        "payment_method",
        "fare_class_category",
    )
    valid_strings = pl.all_horizontal(
        pl.col(column).str.strip_chars().str.len_chars() > 0
        for column in non_empty_columns
    )
    valid_row = (
        pl.col("observed_at_local").is_not_null()
        & pl.col("observed_at_utc").is_not_null()
        & (pl.col("timezone") == SUBWAY_LOCAL_TIMEZONE)
        & valid_strings
        & pl.col("ridership").is_finite()
        & (pl.col("ridership") >= 0)
        & pl.col("transfers").is_finite()
        & (pl.col("transfers") >= 0)
        & (pl.col("transfers") <= pl.col("ridership"))
        & pl.col("latitude").is_finite()
        & pl.col("latitude").is_between(-90, 90, closed="both")
        & pl.col("longitude").is_finite()
        & pl.col("longitude").is_between(-180, 180, closed="both")
        & pl.col("ingested_at").is_not_null()
    ).fill_null(False)
    invalid_count = dataframe.select((~valid_row).sum()).item()
    if invalid_count:
        raise ValueError(
            f"Silver subway validation failed for {invalid_count} row(s)"
        )

    grain = dataframe.select(SUBWAY_GRAIN_COLUMNS)
    if grain.is_duplicated().any():
        raise ValueError("Silver subway data contains duplicate grain values")

    return dataframe
