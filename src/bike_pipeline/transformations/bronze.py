from datetime import UTC, datetime

import polars as pl

from bike_pipeline.validation.models import BIKE_BRONZE_SCHEMA


def transform_source_to_bronze(
    dataframe: pl.DataFrame,
    *,
    ingested_at: datetime | None = None,
) -> pl.DataFrame:
    """Create a typed Bronze frame and stamp every row consistently."""
    ingestion_time = datetime.now(UTC) if ingested_at is None else ingested_at
    if ingestion_time.tzinfo is None or ingestion_time.utcoffset() is None:
        raise ValueError("ingested_at must be timezone-aware")

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
        pl.lit(ingestion_time.astimezone(UTC))
        .cast(pl.Datetime(time_unit="us", time_zone="UTC"))
        .alias("ingested_at"),
    )
