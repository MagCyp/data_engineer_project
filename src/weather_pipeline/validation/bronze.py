import polars as pl

BRONZE_REQUIRED_COLUMNS = {
    "location",
    "timezone",
    "time",
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "rain",
    "wind_speed_10m",
    "ingested_at",
}


def validate_bronze_weather(dataframe: pl.DataFrame) -> pl.DataFrame:
    """Validate bronze weather observations and return them unchanged."""
    missing_columns = BRONZE_REQUIRED_COLUMNS.difference(dataframe.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing bronze columns: {missing}")

    for column in ("time", "ingested_at"):
        dtype = dataframe.schema[column]
        if not isinstance(dtype, pl.Datetime) or dtype.time_zone != "UTC":
            raise ValueError(f"Bronze column '{column}' must use UTC timezone")

    valid_row = (
        pl.col("location").is_not_null()
        & (pl.col("location").str.strip_chars() != "")
        & pl.col("timezone").is_not_null()
        & (pl.col("timezone").str.strip_chars() != "")
        & pl.col("time").is_not_null()
        & pl.col("temperature_2m").is_not_null()
        & pl.col("temperature_2m").is_finite()
        & pl.col("relative_humidity_2m").is_between(0, 100)
        & pl.col("precipitation").is_not_null()
        & pl.col("precipitation").is_finite()
        & (pl.col("precipitation") >= 0)
        & pl.col("rain").is_not_null()
        & pl.col("rain").is_finite()
        & (pl.col("rain") >= 0)
        & pl.col("wind_speed_10m").is_not_null()
        & pl.col("wind_speed_10m").is_finite()
        & (pl.col("wind_speed_10m") >= 0)
        & pl.col("ingested_at").is_not_null()
    ).fill_null(False)

    invalid_count = dataframe.select((~valid_row).sum()).item()
    if invalid_count:
        raise ValueError(
            f"Bronze weather validation failed for {invalid_count} row(s)"
        )

    return dataframe
