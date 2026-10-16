from datetime import UTC, datetime

import polars as pl

from bike_pipeline.validation.models import BIKE_BRONZE_SCHEMA
from common.validation import normalize_utc_datetime


def transform_source_to_bronze(
    dataframe: pl.DataFrame,
    *,
    ingested_at: datetime | None = None,
) -> pl.DataFrame:
    """Create a typed Bronze frame and stamp every row consistently."""
    ingestion_time = datetime.now(UTC) if ingested_at is None else ingested_at
    ingestion_time = normalize_utc_datetime(ingestion_time)

    missing_columns = set(BIKE_BRONZE_SCHEMA.names()[:-1]).difference(
        dataframe.columns
    )
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing bike source columns: {missing}")

    return dataframe.select(
        pl.col("countid").cast(pl.Int64),
        pl.col("id").cast(pl.Int64),
        pl.col("date").cast(pl.Datetime(time_unit="us")),
        pl.col("counts").cast(pl.Int64),
        pl.col("status").cast(pl.Int64),
        pl.lit(ingestion_time)
        .cast(pl.Datetime(time_unit="us", time_zone="UTC"))
        .alias("ingested_at"),
    )
