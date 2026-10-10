import polars as pl

SILVER_COLUMNS = [
    "location",
    "timezone",
    "observed_at",
    "temperature_c",
    "relative_humidity_pct",
    "precipitation_mm",
    "rain_mm",
    "wind_speed_kmh",
    "ingested_at",
]


def transform_bronze_to_silver(dataframe: pl.DataFrame) -> pl.DataFrame:
    """Rename, deduplicate, and sort validated bronze observations."""
    silver = dataframe.select(
        pl.col("location").str.strip_chars(),
        pl.col("timezone").str.strip_chars(),
        pl.col("time").alias("observed_at"),
        pl.col("temperature_2m").alias("temperature_c"),
        pl.col("relative_humidity_2m").alias("relative_humidity_pct"),
        pl.col("precipitation").alias("precipitation_mm"),
        pl.col("rain").alias("rain_mm"),
        pl.col("wind_speed_10m").alias("wind_speed_kmh"),
        pl.col("ingested_at"),
    )

    return (
        silver.sort("ingested_at")
        .unique(
            subset=["location", "observed_at"],
            keep="last",
        )
        .select(SILVER_COLUMNS)
        .sort(["location", "observed_at"])
    )
