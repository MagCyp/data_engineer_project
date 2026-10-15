from datetime import UTC, datetime

import polars as pl
import pytest

from bike_pipeline.validation import (
    BIKE_BRONZE_SCHEMA,
    BIKE_SILVER_SCHEMA,
    validate_bronze_bike,
    validate_silver_bike,
)


def bronze_dataframe() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "countid": [1],
            "id": [101],
            "date": [datetime(2023, 6, 3, 0, 15)],
            "counts": [9],
            "status": [0],
            "ingested_at": [datetime(2026, 10, 15, 12, 0, tzinfo=UTC)],
        },
        schema=BIKE_BRONZE_SCHEMA,
    )


def silver_dataframe() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "record_id": [1],
            "counter_id": [101],
            "timezone": ["America/New_York"],
            "observed_at_local": [datetime(2023, 6, 3, 0, 15)],
            "observed_at_utc": [
                datetime(2023, 6, 3, 4, 15, tzinfo=UTC)
            ],
            "bike_count": [9],
            "status": [0],
            "ingested_at": [datetime(2026, 10, 15, 12, 0, tzinfo=UTC)],
        },
        schema=BIKE_SILVER_SCHEMA,
    )


def test_validate_bronze_bike_accepts_valid_data() -> None:
    dataframe = bronze_dataframe()

    assert validate_bronze_bike(dataframe) is dataframe


def test_validate_bronze_bike_rejects_duplicate_record_ids() -> None:
    dataframe = pl.concat([bronze_dataframe(), bronze_dataframe()])

    with pytest.raises(ValueError, match="duplicate countid"):
        validate_bronze_bike(dataframe)


def test_validate_silver_bike_accepts_valid_data() -> None:
    dataframe = silver_dataframe()

    assert validate_silver_bike(dataframe) is dataframe


def test_validate_silver_bike_rejects_negative_count() -> None:
    dataframe = silver_dataframe().with_columns(
        pl.lit(-1, dtype=pl.Int64).alias("bike_count")
    )

    with pytest.raises(ValueError, match="failed for 1 row"):
        validate_silver_bike(dataframe)
