import polars as pl

SILVER_REQUIRED_COLUMNS = {
    "location",
    "timezone",
    "observed_at",
    "temperature_c",
    "relative_humidity_pct",
    "precipitation_mm",
    "rain_mm",
    "wind_speed_kmh",
    "ingested_at",
}


def validate_silver_weather(dataframe: pl.DataFrame) -> pl.DataFrame:
    """Validate silver weather observations and return them unchanged."""
    missing_columns = SILVER_REQUIRED_COLUMNS.difference(dataframe.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing silver columns: {missing}")

    valid_row = (
        pl.col("location").is_not_null()
        & (pl.col("location").str.strip_chars() != "")
        & pl.col("timezone").is_not_null()
        & (pl.col("timezone").str.strip_chars() != "")
        & pl.col("observed_at").is_not_null()
        & pl.col("temperature_c").is_not_null()
        & pl.col("temperature_c").is_finite()
        & pl.col("relative_humidity_pct").is_between(0, 100)
        & pl.col("precipitation_mm").is_not_null()
        & pl.col("precipitation_mm").is_finite()
        & (pl.col("precipitation_mm") >= 0)
        & pl.col("rain_mm").is_not_null()
        & pl.col("rain_mm").is_finite()
        & (pl.col("rain_mm") >= 0)
        & pl.col("wind_speed_kmh").is_not_null()
        & pl.col("wind_speed_kmh").is_finite()
        & (pl.col("wind_speed_kmh") >= 0)
        & pl.col("ingested_at").is_not_null()
    ).fill_null(False)

    invalid_count = dataframe.select((~valid_row).sum()).item()
    if invalid_count:
        raise ValueError(
            f"Silver weather validation failed for {invalid_count} row(s)"
        )

    return dataframe
