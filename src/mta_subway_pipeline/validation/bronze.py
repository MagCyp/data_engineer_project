import polars as pl

from .models import SUBWAY_BRONZE_SCHEMA


def validate_bronze_subway(dataframe: pl.DataFrame) -> pl.DataFrame:
    """Validate parsed subway source records and return them unchanged."""
    missing_columns = set(SUBWAY_BRONZE_SCHEMA.names()).difference(
        dataframe.columns
    )
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing Bronze subway columns: {missing}")

    for column, expected_dtype in SUBWAY_BRONZE_SCHEMA.items():
        if dataframe.schema[column] != expected_dtype:
            raise ValueError(
                f"Bronze subway column '{column}' must use {expected_dtype}"
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
        pl.col("transit_timestamp").is_not_null()
        & (pl.col("transit_timestamp").dt.minute() == 0)
        & (pl.col("transit_timestamp").dt.second() == 0)
        & (pl.col("transit_timestamp").dt.microsecond() == 0)
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
            f"Bronze subway validation failed for {invalid_count} row(s)"
        )

    return dataframe
