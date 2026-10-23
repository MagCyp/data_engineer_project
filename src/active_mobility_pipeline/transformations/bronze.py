from collections.abc import Iterable
from datetime import UTC, datetime

import polars as pl

from active_mobility_pipeline.validation import (
    ACTIVE_MOBILITY_COUNT_BRONZE_SCHEMA,
    ACTIVE_MOBILITY_COUNT_SOURCE_SCHEMA,
    ACTIVE_MOBILITY_SENSOR_BRONZE_SCHEMA,
    ACTIVE_MOBILITY_SENSOR_SOURCE_SCHEMA,
    ActiveMobilityCountSourceRecord,
    ActiveMobilitySensorSourceRecord,
)
from common.validation import normalize_utc_datetime
from storage.files import models_to_dataframe


def _ingestion_time(value: datetime | None) -> datetime:
    timestamp = datetime.now(UTC) if value is None else value
    return normalize_utc_datetime(timestamp)


def transform_count_source_to_bronze(
    records: Iterable[ActiveMobilityCountSourceRecord],
    *,
    ingested_at: datetime | None = None,
) -> pl.DataFrame:
    source = models_to_dataframe(
        records,
        schema=ACTIVE_MOBILITY_COUNT_SOURCE_SCHEMA,
    )
    return source.with_columns(
        pl.lit(_ingestion_time(ingested_at))
        .cast(pl.Datetime(time_unit="us", time_zone="UTC"))
        .alias("ingested_at")
    ).select(ACTIVE_MOBILITY_COUNT_BRONZE_SCHEMA.names())


def transform_sensor_source_to_bronze(
    records: Iterable[ActiveMobilitySensorSourceRecord],
    *,
    ingested_at: datetime | None = None,
) -> pl.DataFrame:
    source = models_to_dataframe(
        records,
        schema=ACTIVE_MOBILITY_SENSOR_SOURCE_SCHEMA,
    )
    return source.with_columns(
        pl.lit(_ingestion_time(ingested_at))
        .cast(pl.Datetime(time_unit="us", time_zone="UTC"))
        .alias("ingested_at")
    ).select(ACTIVE_MOBILITY_SENSOR_BRONZE_SCHEMA.names())
