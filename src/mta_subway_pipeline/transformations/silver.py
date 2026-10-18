import polars as pl

from mta_subway_pipeline.validation.models import (
    SUBWAY_AMBIGUOUS_TIME_POLICY,
    SUBWAY_BRONZE_SCHEMA,
    SUBWAY_GRAIN_COLUMNS,
    SUBWAY_LOCAL_TIMEZONE,
    SUBWAY_SILVER_SCHEMA,
)

SILVER_COLUMNS = SUBWAY_SILVER_SCHEMA.names()
STRING_COLUMNS = (
    "transit_mode",
    "station_complex_id",
    "station_complex",
    "borough",
    "payment_method",
    "fare_class_category",
)


def transform_bronze_to_silver(dataframe: pl.DataFrame) -> pl.DataFrame:
    missing_columns = set(SUBWAY_BRONZE_SCHEMA.names()).difference(
        dataframe.columns
    )
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing subway Bronze columns: {missing}")

    silver = dataframe.select(
        pl.col("transit_timestamp").alias("observed_at_local"),
        pl.col("transit_timestamp")
        .dt.replace_time_zone(
            SUBWAY_LOCAL_TIMEZONE,
            ambiguous=SUBWAY_AMBIGUOUS_TIME_POLICY,
            non_existent="null",
        )
        .dt.convert_time_zone("UTC")
        .alias("observed_at_utc"),
        pl.lit(SUBWAY_LOCAL_TIMEZONE).alias("timezone"),
        *(pl.col(column).str.strip_chars() for column in STRING_COLUMNS),
        pl.col("ridership"),
        pl.col("transfers"),
        pl.col("latitude"),
        pl.col("longitude"),
        pl.col("ingested_at"),
    )

    nonexistent_times = silver.filter(pl.col("observed_at_utc").is_null())
    if not nonexistent_times.is_empty():
        raise ValueError(
            "Subway data contains local timestamps that do not exist in "
            f"{SUBWAY_LOCAL_TIMEZONE} because of the DST transition"
        )

    return (
        silver.sort("ingested_at")
        .unique(subset=list(SUBWAY_GRAIN_COLUMNS), keep="last")
        .select(SILVER_COLUMNS)
        .sort(list(SUBWAY_GRAIN_COLUMNS))
    )
