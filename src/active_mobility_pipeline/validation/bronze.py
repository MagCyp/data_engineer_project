import polars as pl

from common.validation import (
    non_empty_strings,
    require_dataframe_schema,
    require_unique_columns,
    require_valid_rows,
)

from .models import (
    ACTIVE_MOBILITY_COUNT_BRONZE_SCHEMA,
    ACTIVE_MOBILITY_DIRECTIONS,
    ACTIVE_MOBILITY_INTERVALS,
    ACTIVE_MOBILITY_SENSOR_BRONZE_SCHEMA,
    ACTIVE_MOBILITY_STATUSES,
    ACTIVE_MOBILITY_TRAVEL_MODES,
)


def validate_bronze_active_mobility_counts(
    dataframe: pl.DataFrame,
) -> pl.DataFrame:
    require_dataframe_schema(
        dataframe,
        ACTIVE_MOBILITY_COUNT_BRONZE_SCHEMA,
        name="Bronze active mobility counts",
    )
    valid_row = (
        non_empty_strings(("sensor_id", "flowid"))
        & pl.col("travelmode").is_in(list(ACTIVE_MOBILITY_TRAVEL_MODES))
        & pl.col("direction").is_in(list(ACTIVE_MOBILITY_DIRECTIONS))
        & pl.col("granularity").is_in(list(ACTIVE_MOBILITY_INTERVALS))
        & (pl.col("counts").is_null() | (pl.col("counts") >= 0))
        & pl.col("status").is_in(list(ACTIVE_MOBILITY_STATUSES))
        & pl.col("timestamp").is_not_null()
        & pl.col("ingested_at").is_not_null()
    )
    require_valid_rows(
        dataframe,
        valid_row,
        name="Bronze active mobility counts",
    )
    require_unique_columns(
        dataframe,
        ("flowid", "timestamp", "granularity"),
        message="Bronze active mobility counts contain duplicate source keys",
    )
    return dataframe


def validate_bronze_active_mobility_sensors(
    dataframe: pl.DataFrame,
) -> pl.DataFrame:
    require_dataframe_schema(
        dataframe,
        ACTIVE_MOBILITY_SENSOR_BRONZE_SCHEMA,
        name="Bronze active mobility sensors",
    )
    if dataframe.is_empty():
        raise ValueError("Bronze active mobility sensor snapshot must not be empty")
    valid_coordinates = (
        pl.col("lat").is_null() & pl.col("lon").is_null()
    ) | (
        pl.col("lat").is_between(-90, 90, closed="both")
        & pl.col("lon").is_between(-180, 180, closed="both")
    )
    valid_row = (
        non_empty_strings(("id", "name", "travelmodes", "domain_name"))
        & valid_coordinates
        & pl.col("firstdata").is_not_null()
        & pl.col("lastdata").is_not_null()
        & (pl.col("firstdata") <= pl.col("lastdata"))
        & pl.col("granularity").is_in(list(ACTIVE_MOBILITY_INTERVALS))
        & pl.col("ingested_at").is_not_null()
    )
    require_valid_rows(
        dataframe,
        valid_row,
        name="Bronze active mobility sensors",
    )
    return dataframe
