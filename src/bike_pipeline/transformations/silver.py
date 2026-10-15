import polars as pl

from bike_pipeline.validation.models import (
    BIKE_AMBIGUOUS_TIME_POLICY,
    BIKE_LOCAL_TIMEZONE,
    BIKE_SILVER_SCHEMA,
    BIKE_SOURCE_TIMEZONE_MAP,
)

SILVER_COLUMNS = BIKE_SILVER_SCHEMA.names()


def _counter_timezones(counter_data: pl.DataFrame) -> pl.DataFrame:
    required_columns = {"id", "timezone"}
    missing_columns = required_columns.difference(counter_data.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing bike counter metadata columns: {missing}")

    timezones = counter_data.select("id", "timezone")
    duplicate_ids = timezones.filter(pl.col("id").is_duplicated())
    if not duplicate_ids.is_empty():
        ids = duplicate_ids["id"].unique().sort().to_list()
        raise ValueError(f"Bike counter metadata contains duplicate ids: {ids}")

    unsupported = timezones.filter(
        ~pl.col("timezone").is_in(list(BIKE_SOURCE_TIMEZONE_MAP))
    )
    if not unsupported.is_empty():
        values = unsupported["timezone"].unique().sort().to_list()
        raise ValueError(f"Unsupported bike counter timezones: {values}")

    return timezones.with_columns(
        pl.col("timezone").replace(BIKE_SOURCE_TIMEZONE_MAP)
    )


def transform_bronze_to_silver(
    dataframe: pl.DataFrame,
    counter_data: pl.DataFrame,
) -> pl.DataFrame:
    """Enrich Bronze rows and convert New York local time to UTC."""
    enriched = dataframe.join(
        _counter_timezones(counter_data),
        left_on="id",
        right_on="id",
        how="left",
        validate="m:1",
    )

    missing_counter_ids = (
        enriched.filter(pl.col("timezone").is_null())["id"]
        .unique()
        .sort()
        .to_list()
    )
    if missing_counter_ids:
        raise ValueError(
            "Missing counter metadata for bike counter ids: "
            f"{missing_counter_ids}"
        )

    silver = enriched.select(
        pl.col("countid").alias("record_id"),
        pl.col("id").alias("counter_id"),
        pl.col("timezone"),
        pl.col("date").alias("observed_at_local"),
        pl.col("date")
        .dt.replace_time_zone(
            BIKE_LOCAL_TIMEZONE,
            ambiguous=BIKE_AMBIGUOUS_TIME_POLICY,
            non_existent="null",
        )
        .dt.convert_time_zone("UTC")
        .alias("observed_at_utc"),
        pl.col("counts").alias("bike_count"),
        pl.col("status"),
        pl.col("ingested_at"),
    )

    nonexistent_times = silver.filter(pl.col("observed_at_utc").is_null())
    if not nonexistent_times.is_empty():
        raise ValueError(
            "Bike data contains local timestamps that do not exist in "
            f"{BIKE_LOCAL_TIMEZONE} because of the DST transition"
        )

    return silver.select(SILVER_COLUMNS).sort(
        ["counter_id", "observed_at_utc", "record_id"]
    )
