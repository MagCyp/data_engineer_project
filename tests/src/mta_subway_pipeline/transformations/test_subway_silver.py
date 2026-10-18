from datetime import UTC, datetime

import polars as pl
import pytest

from mta_subway_pipeline.transformations import transform_bronze_to_silver
from mta_subway_pipeline.validation import (
    SUBWAY_BRONZE_SCHEMA,
    SUBWAY_LOCAL_TIMEZONE,
    SUBWAY_SILVER_SCHEMA,
)


def bronze_row(timestamp: datetime, **overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "transit_timestamp": timestamp,
        "transit_mode": " subway ",
        "station_complex_id": "158",
        "station_complex": " 86 St (C,B) ",
        "borough": "Manhattan",
        "payment_method": "omny",
        "fare_class_category": "OMNY - Full Fare",
        "ridership": 451.0,
        "transfers": 26.0,
        "latitude": 40.78587,
        "longitude": -73.96892,
        "georeference": {
            "type": "Point",
            "coordinates": [-73.96892, 40.78587],
        },
        "ingested_at": datetime(2026, 10, 18, 12, tzinfo=UTC),
    }
    row.update(overrides)
    return row


def bronze_dataframe(rows: list[dict[str, object]]) -> pl.DataFrame:
    return pl.from_dicts(rows, schema=SUBWAY_BRONZE_SCHEMA, strict=True)


def test_transform_bronze_to_silver_converts_new_york_time_to_utc() -> None:
    bronze = bronze_dataframe(
        [
            bronze_row(datetime(2025, 7, 1, 12)),
            bronze_row(
                datetime(2025, 12, 1, 12),
                station_complex_id="159",
            ),
        ]
    )

    result = transform_bronze_to_silver(bronze)

    assert result.schema == SUBWAY_SILVER_SCHEMA
    assert result["observed_at_utc"].to_list() == [
        datetime(2025, 7, 1, 16, tzinfo=UTC),
        datetime(2025, 12, 1, 17, tzinfo=UTC),
    ]
    assert result["timezone"].to_list() == [
        SUBWAY_LOCAL_TIMEZONE,
        SUBWAY_LOCAL_TIMEZONE,
    ]
    assert result.item(0, "transit_mode") == "subway"
    assert result.item(0, "station_complex") == "86 St (C,B)"


def test_transform_bronze_to_silver_keeps_latest_duplicate() -> None:
    timestamp = datetime(2025, 7, 1, 12)
    bronze = bronze_dataframe(
        [
            bronze_row(
                timestamp,
                ridership=400.0,
                ingested_at=datetime(2026, 10, 18, 11, tzinfo=UTC),
            ),
            bronze_row(timestamp, ridership=451.0),
        ]
    )

    result = transform_bronze_to_silver(bronze)

    assert result.height == 1
    assert result.item(0, "ridership") == 451.0


def test_transform_bronze_to_silver_uses_explicit_fall_back_policy() -> None:
    bronze = bronze_dataframe([bronze_row(datetime(2025, 11, 2, 1))])

    result = transform_bronze_to_silver(bronze)

    assert result.item(0, "observed_at_utc") == datetime(
        2025,
        11,
        2,
        5,
        tzinfo=UTC,
    )


def test_transform_bronze_to_silver_rejects_nonexistent_local_time() -> None:
    bronze = bronze_dataframe([bronze_row(datetime(2025, 3, 9, 2))])

    with pytest.raises(ValueError, match="do not exist"):
        transform_bronze_to_silver(bronze)
