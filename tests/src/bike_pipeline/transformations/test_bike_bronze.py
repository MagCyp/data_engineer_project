from datetime import UTC, datetime

import polars as pl
import pytest

from bike_pipeline.transformations import transform_source_to_bronze
from bike_pipeline.validation import BIKE_BRONZE_SCHEMA


def test_transform_source_to_bronze_adds_one_ingestion_timestamp() -> None:
    source = pl.DataFrame(
        {
            "countid": [1, 2],
            "id": [101, 101],
            "date": [
                datetime(2023, 6, 3, 0, 0),
                datetime(2023, 6, 3, 0, 15),
            ],
            "counts": [27, 9],
            "status": [0, 4],
        }
    )
    ingested_at = datetime(2026, 10, 15, 12, 0, tzinfo=UTC)

    result = transform_source_to_bronze(source, ingested_at=ingested_at)

    assert result.schema == BIKE_BRONZE_SCHEMA
    assert result["ingested_at"].to_list() == [ingested_at, ingested_at]


def test_transform_source_to_bronze_rejects_naive_ingestion_time() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        transform_source_to_bronze(
            pl.DataFrame(),
            ingested_at=datetime(2026, 10, 15, 12, 0),
        )
