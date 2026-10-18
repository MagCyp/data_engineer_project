from datetime import UTC, datetime, timedelta, timezone

import pytest

from mta_subway_pipeline.transformations import transform_source_to_bronze
from mta_subway_pipeline.validation import (
    SUBWAY_BRONZE_SCHEMA,
    SubwaySourceRecord,
)


def source_record(timestamp: datetime) -> SubwaySourceRecord:
    return SubwaySourceRecord(
        transit_timestamp=timestamp,
        transit_mode="subway",
        station_complex_id="158",
        station_complex="86 St (C,B)",
        borough="Manhattan",
        payment_method="omny",
        fare_class_category="OMNY - Full Fare",
        ridership=451.0,
        transfers=26.0,
        latitude=40.78587,
        longitude=-73.96892,
        georeference={
            "type": "Point",
            "coordinates": (-73.96892, 40.78587),
        },
    )


def test_transform_source_to_bronze_creates_typed_frame() -> None:
    ingested_at = datetime(
        2026,
        10,
        18,
        14,
        tzinfo=timezone(timedelta(hours=2)),
    )

    result = transform_source_to_bronze(
        [source_record(datetime(2025, 1, 15, 8))],
        ingested_at=ingested_at,
    )

    assert result.schema == SUBWAY_BRONZE_SCHEMA
    assert result.item(0, "transit_timestamp") == datetime(2025, 1, 15, 8)
    assert result.item(0, "ingested_at") == datetime(
        2026,
        10,
        18,
        12,
        tzinfo=UTC,
    )


def test_transform_source_to_bronze_supports_empty_batch() -> None:
    result = transform_source_to_bronze(
        [],
        ingested_at=datetime(2026, 10, 18, 12, tzinfo=UTC),
    )

    assert result.is_empty()
    assert result.schema == SUBWAY_BRONZE_SCHEMA


def test_transform_source_to_bronze_rejects_naive_ingestion_time() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        transform_source_to_bronze(
            [],
            ingested_at=datetime(2026, 10, 18, 12),
        )
