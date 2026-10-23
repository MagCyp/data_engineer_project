import polars as pl

from common.validation import (
    non_empty_strings,
    require_dataframe_schema,
    require_unique_columns,
    require_valid_rows,
)

from .models import (
    ACTIVE_MOBILITY_COUNT_SILVER_SCHEMA,
    ACTIVE_MOBILITY_DIRECTIONS,
    ACTIVE_MOBILITY_INTERVALS,
    ACTIVE_MOBILITY_LOCAL_TIMEZONE,
    ACTIVE_MOBILITY_SENSOR_SILVER_SCHEMA,
    ACTIVE_MOBILITY_STATUSES,
    ACTIVE_MOBILITY_TRAVEL_MODES,
)


def validate_silver_active_mobility_counts(
    dataframe: pl.DataFrame,
) -> pl.DataFrame:
    require_dataframe_schema(
        dataframe,
        ACTIVE_MOBILITY_COUNT_SILVER_SCHEMA,
        name="Silver active mobility counts",
    )
    valid_row = (
        non_empty_strings(("sensor_id", "flow_id"))
        & pl.col("travel_mode").is_in(list(ACTIVE_MOBILITY_TRAVEL_MODES))
        & pl.col("direction").is_in(list(ACTIVE_MOBILITY_DIRECTIONS))
        & (pl.col("timezone") == ACTIVE_MOBILITY_LOCAL_TIMEZONE)
        & pl.col("observed_at_local").is_not_null()
        & pl.col("observed_at_utc").is_not_null()
        & pl.col("interval_minutes").is_in(
            list(ACTIVE_MOBILITY_INTERVALS.values())
        )
        & (
            pl.col("mobility_count").is_null()
            | (pl.col("mobility_count") >= 0)
        )
        & pl.col("source_status").is_in(list(ACTIVE_MOBILITY_STATUSES))
        & pl.col("ingested_at").is_not_null()
    )
    require_valid_rows(
        dataframe,
        valid_row,
        name="Silver active mobility counts",
    )
    require_unique_columns(
        dataframe,
        ("flow_id", "observed_at_utc", "interval_minutes"),
        message="Silver active mobility counts contain duplicate keys",
    )
    return dataframe


def validate_silver_active_mobility_sensors(
    dataframe: pl.DataFrame,
) -> pl.DataFrame:
    require_dataframe_schema(
        dataframe,
        ACTIVE_MOBILITY_SENSOR_SILVER_SCHEMA,
        name="Silver active mobility sensors",
    )
    valid_row = (
        non_empty_strings(
            ("sensor_id", "sensor_name", "travel_modes", "operator_name")
        )
        & pl.col("latitude").is_between(-90, 90, closed="both")
        & pl.col("longitude").is_between(-180, 180, closed="both")
        & (pl.col("timezone") == ACTIVE_MOBILITY_LOCAL_TIMEZONE)
        & pl.col("first_observed_at_local").is_not_null()
        & pl.col("last_observed_at_local").is_not_null()
        & (
            pl.col("first_observed_at_local")
            <= pl.col("last_observed_at_local")
        )
        & pl.col("recording_interval_minutes").is_in(
            list(ACTIVE_MOBILITY_INTERVALS.values())
        )
        & pl.col("ingested_at").is_not_null()
    )
    require_valid_rows(
        dataframe,
        valid_row,
        name="Silver active mobility sensors",
    )
    require_unique_columns(
        dataframe,
        "sensor_id",
        message="Silver active mobility sensors contain duplicate sensor ids",
    )
    return dataframe
