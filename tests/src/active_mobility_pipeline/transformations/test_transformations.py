from datetime import UTC, datetime

import pytest

from active_mobility_pipeline.transformations import (
    transform_count_bronze_to_silver,
    transform_count_source_to_bronze,
    transform_sensor_bronze_to_silver,
    transform_sensor_source_to_bronze,
)
from active_mobility_pipeline.validation import (
    ACTIVE_MOBILITY_COUNT_BRONZE_SCHEMA,
    ACTIVE_MOBILITY_COUNT_SILVER_SCHEMA,
    ACTIVE_MOBILITY_SENSOR_BRONZE_SCHEMA,
    ACTIVE_MOBILITY_SENSOR_SILVER_SCHEMA,
    ActiveMobilityCountSourceRecord,
    ActiveMobilitySensorSourceRecord,
)


def count_record() -> ActiveMobilityCountSourceRecord:
    return ActiveMobilityCountSourceRecord(
        sensor_id="100",
        travelmode="pedestrian",
        direction="in",
        flowid="101",
        flowname="Pedestrian IN",
        timestamp=datetime(2025, 1, 15, 8, 15),
        granularity="PT15M",
        counts=18,
        status="raw",
    )


def sensor_record(
    *,
    name: str = "Shared Counter",
    counter_id: str | None = None,
    latitude: float | None = 40.7,
    longitude: float | None = -73.9,
) -> ActiveMobilitySensorSourceRecord:
    return ActiveMobilitySensorSourceRecord(
        id="100",
        name=name,
        lat=latitude,
        lon=longitude,
        firstdata=datetime(2022, 9, 2, 11, 15),
        lastdata=datetime(2026, 10, 22, 1, 15),
        granularity="PT15M",
        travelmodes="bike, pedestrian",
        directional=True,
        hastimestampeddata=False,
        hasweather=True,
        counters_id=counter_id,
        domain_name="New York City DOT",
    )


def test_count_transform_normalizes_api_record() -> None:
    ingested_at = datetime(2026, 10, 23, 12, tzinfo=UTC)
    bronze = transform_count_source_to_bronze(
        [count_record()],
        ingested_at=ingested_at,
    )
    silver = transform_count_bronze_to_silver(bronze)

    assert bronze.schema == ACTIVE_MOBILITY_COUNT_BRONZE_SCHEMA
    assert silver.schema == ACTIVE_MOBILITY_COUNT_SILVER_SCHEMA
    assert silver.item(0, "travel_mode") == "pedestrian"
    assert silver.item(0, "interval_minutes") == 15
    assert silver.item(0, "observed_at_utc") == datetime(
        2025,
        1,
        15,
        13,
        15,
        tzinfo=UTC,
    )


def test_sensor_transform_collapses_hardware_history() -> None:
    ingested_at = datetime(2026, 10, 23, 12, tzinfo=UTC)
    bronze = transform_sensor_source_to_bronze(
        [
            sensor_record(counter_id="old"),
            sensor_record(counter_id="current"),
        ],
        ingested_at=ingested_at,
    )
    silver = transform_sensor_bronze_to_silver(bronze)

    assert bronze.schema == ACTIVE_MOBILITY_SENSOR_BRONZE_SCHEMA
    assert silver.schema == ACTIVE_MOBILITY_SENSOR_SILVER_SCHEMA
    assert silver.height == 1
    assert silver.item(0, "travel_modes") == "bike, pedestrian"


def test_sensor_transform_rejects_conflicting_attributes() -> None:
    bronze = transform_sensor_source_to_bronze(
        [sensor_record(), sensor_record(name="Different Name")],
        ingested_at=datetime(2026, 10, 23, 12, tzinfo=UTC),
    )

    with pytest.raises(ValueError, match="attributes conflict"):
        transform_sensor_bronze_to_silver(bronze)


def test_sensor_transform_excludes_missing_coordinate_pair() -> None:
    bronze = transform_sensor_source_to_bronze(
        [sensor_record(latitude=None, longitude=None)],
        ingested_at=datetime(2026, 10, 23, 12, tzinfo=UTC),
    )

    silver = transform_sensor_bronze_to_silver(bronze)

    assert silver.is_empty()
