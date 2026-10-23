import polars as pl

from active_mobility_pipeline.validation import (
    ACTIVE_MOBILITY_AMBIGUOUS_TIME_POLICY,
    ACTIVE_MOBILITY_COUNT_BRONZE_SCHEMA,
    ACTIVE_MOBILITY_COUNT_SILVER_SCHEMA,
    ACTIVE_MOBILITY_INTERVALS,
    ACTIVE_MOBILITY_LOCAL_TIMEZONE,
    ACTIVE_MOBILITY_SENSOR_BRONZE_SCHEMA,
    ACTIVE_MOBILITY_SENSOR_SILVER_SCHEMA,
)


def _require_columns(
    dataframe: pl.DataFrame,
    schema: pl.Schema,
    *,
    name: str,
) -> None:
    missing_columns = set(schema.names()).difference(dataframe.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing {name} columns: {missing}")


def transform_count_bronze_to_silver(
    dataframe: pl.DataFrame,
) -> pl.DataFrame:
    _require_columns(
        dataframe,
        ACTIVE_MOBILITY_COUNT_BRONZE_SCHEMA,
        name="active mobility count Bronze",
    )
    silver = dataframe.select(
        pl.col("sensor_id").str.strip_chars(),
        pl.col("flowid").str.strip_chars().alias("flow_id"),
        pl.col("flowname").str.strip_chars().alias("flow_name"),
        pl.col("travelmode").alias("travel_mode"),
        pl.col("direction"),
        pl.lit(ACTIVE_MOBILITY_LOCAL_TIMEZONE).alias("timezone"),
        pl.col("timestamp").alias("observed_at_local"),
        pl.col("timestamp")
        .dt.replace_time_zone(
            ACTIVE_MOBILITY_LOCAL_TIMEZONE,
            ambiguous=ACTIVE_MOBILITY_AMBIGUOUS_TIME_POLICY,
            non_existent="null",
        )
        .dt.convert_time_zone("UTC")
        .alias("observed_at_utc"),
        pl.col("granularity")
        .replace(ACTIVE_MOBILITY_INTERVALS)
        .cast(pl.Int64)
        .alias("interval_minutes"),
        pl.col("counts").alias("mobility_count"),
        pl.col("status").alias("source_status"),
        pl.col("ingested_at"),
    )
    if silver["observed_at_utc"].null_count():
        raise ValueError(
            "Active mobility data contains local timestamps that do not exist "
            f"in {ACTIVE_MOBILITY_LOCAL_TIMEZONE} because of the DST transition"
        )
    return silver.select(ACTIVE_MOBILITY_COUNT_SILVER_SCHEMA.names()).sort(
        ["observed_at_utc", "flow_id", "interval_minutes"]
    )


def transform_sensor_bronze_to_silver(
    dataframe: pl.DataFrame,
) -> pl.DataFrame:
    _require_columns(
        dataframe,
        ACTIVE_MOBILITY_SENSOR_BRONZE_SCHEMA,
        name="active mobility sensor Bronze",
    )
    sensors = dataframe.filter(
        pl.col("lat").is_not_null() & pl.col("lon").is_not_null()
    ).select(
        pl.col("id").str.strip_chars().alias("sensor_id"),
        pl.col("name").str.strip_chars().alias("sensor_name"),
        pl.col("lat").alias("latitude"),
        pl.col("lon").alias("longitude"),
        pl.lit(ACTIVE_MOBILITY_LOCAL_TIMEZONE).alias("timezone"),
        pl.col("firstdata").alias("first_observed_at_local"),
        pl.col("lastdata").alias("last_observed_at_local"),
        pl.col("granularity")
        .replace(ACTIVE_MOBILITY_INTERVALS)
        .cast(pl.Int64)
        .alias("recording_interval_minutes"),
        pl.col("travelmodes").str.strip_chars().alias("travel_modes"),
        pl.col("directional").alias("is_directional"),
        pl.col("hastimestampeddata").alias("has_timestamped_data"),
        pl.col("hasweather").alias("has_weather"),
        pl.col("domain_name").str.strip_chars().alias("operator_name"),
        pl.col("ingested_at"),
    ).unique()
    duplicate_ids = sensors.filter(pl.col("sensor_id").is_duplicated())
    if not duplicate_ids.is_empty():
        ids = duplicate_ids["sensor_id"].unique().sort().to_list()
        raise ValueError(
            "Active mobility sensor attributes conflict for sensor ids: "
            f"{ids}"
        )
    return sensors.select(ACTIVE_MOBILITY_SENSOR_SILVER_SCHEMA.names()).sort(
        "sensor_id"
    )
