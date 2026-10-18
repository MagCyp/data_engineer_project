from collections.abc import Iterable
from datetime import UTC, datetime

import polars as pl

from common.validation import normalize_utc_datetime
from mta_subway_pipeline.validation.models import (
    SUBWAY_BRONZE_SCHEMA,
    SUBWAY_SOURCE_SCHEMA,
    SubwaySourceRecord,
)


def transform_source_to_bronze(
    records: Iterable[SubwaySourceRecord],
    *,
    ingested_at: datetime | None = None,
) -> pl.DataFrame:
    ingestion_time = datetime.now(UTC) if ingested_at is None else ingested_at
    ingestion_time = normalize_utc_datetime(ingestion_time)
    rows = [record.model_dump(mode="python") for record in records]

    source = (
        pl.from_dicts(rows, schema=SUBWAY_SOURCE_SCHEMA, strict=True)
        if rows
        else pl.DataFrame(schema=SUBWAY_SOURCE_SCHEMA)
    )
    return source.with_columns(
        pl.lit(ingestion_time)
        .cast(pl.Datetime(time_unit="us", time_zone="UTC"))
        .alias("ingested_at")
    ).select(SUBWAY_BRONZE_SCHEMA.names())
