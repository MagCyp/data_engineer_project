import polars as pl

from .models import BIKE_ALLOWED_STATUSES, BIKE_BRONZE_SCHEMA


def validate_bronze_bike(dataframe: pl.DataFrame) -> pl.DataFrame:
    """Validate parsed bike source records and return them unchanged."""
    missing_columns = set(BIKE_BRONZE_SCHEMA.names()).difference(dataframe.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing Bronze bike columns: {missing}")

    for column, expected_dtype in BIKE_BRONZE_SCHEMA.items():
        if dataframe.schema[column] != expected_dtype:
            raise ValueError(
                f"Bronze bike column '{column}' must use {expected_dtype}"
            )

    valid_row = (
        (pl.col("countid") > 0)
        & (pl.col("id") > 0)
        & pl.col("date").is_not_null()
        & (pl.col("counts") >= 0)
        & pl.col("status").is_in(list(BIKE_ALLOWED_STATUSES))
        & pl.col("ingested_at").is_not_null()
    ).fill_null(False)
    invalid_count = dataframe.select((~valid_row).sum()).item()
    if invalid_count:
        raise ValueError(
            f"Bronze bike validation failed for {invalid_count} row(s)"
        )

    if dataframe["countid"].is_duplicated().any():
        raise ValueError("Bronze bike data contains duplicate countid values")

    return dataframe
