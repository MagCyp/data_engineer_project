from datetime import UTC, date, datetime
from pathlib import Path

import polars as pl
import pytest

import active_mobility_pipeline.pipeline as pipeline
from active_mobility_pipeline.validation import (
    ACTIVE_MOBILITY_COUNT_BRONZE_SCHEMA,
    ACTIVE_MOBILITY_COUNT_SILVER_SCHEMA,
    ACTIVE_MOBILITY_SENSOR_BRONZE_SCHEMA,
    ACTIVE_MOBILITY_SENSOR_SILVER_SCHEMA,
    ActiveMobilityCountSourceRecord,
    ActiveMobilitySensorSourceRecord,
)


def storage_config(tmp_path: Path) -> dict[str, object]:
    return {
        "storage": {
            "bronze_path": str(
                tmp_path
                / "bronze"
                / "{pipeline_name}"
                / "year={year}"
                / "month={month}"
            ),
            "silver_path": str(
                tmp_path
                / "silver"
                / "{pipeline_name}"
                / "year={year}"
                / "month={month}"
            ),
            "bronze_reference_path": str(
                tmp_path / "bronze" / "{pipeline_name}" / "reference"
            ),
            "silver_reference_path": str(
                tmp_path / "silver" / "{pipeline_name}" / "reference"
            ),
        }
    }


def test_process_month_and_sensor_snapshot_write_expected_parquet(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = storage_config(tmp_path)
    ingested_at = datetime(2026, 10, 23, 12, tzinfo=UTC)
    count = ActiveMobilityCountSourceRecord(
        sensor_id="100",
        travelmode="bike",
        direction="in",
        flowid="101",
        flowname="Bike IN",
        timestamp=datetime(2025, 1, 15, 8),
        granularity="PT15M",
        counts=18,
        status="raw",
    )
    sensor = ActiveMobilitySensorSourceRecord(
        id="100",
        name="Shared Counter",
        lat=40.7,
        lon=-73.9,
        firstdata=datetime(2022, 9, 2, 11, 15),
        lastdata=datetime(2026, 10, 22, 1, 15),
        granularity="PT15M",
        travelmodes="bike, pedestrian",
        directional=True,
        hastimestampeddata=False,
        hasweather=True,
        domain_name="New York City DOT",
    )
    sensor_without_coordinates = ActiveMobilitySensorSourceRecord(
        id="100048744",
        name="Manhattan Bridge Interference Calibration 2018 Bike Counter",
        firstdata=datetime(2013, 7, 25),
        lastdata=datetime(2017, 5, 11, 23, 45),
        granularity="PT15M",
        travelmodes="bike",
        directional=True,
        hastimestampeddata=False,
        hasweather=False,
        domain_name="New York City DOT",
    )
    monkeypatch.setattr(
        pipeline,
        "iter_count_records",
        lambda *args, **kwargs: iter([count]),
    )

    pipeline.process_active_mobility_month(
        config,
        date(2025, 1, 1),
        date(2025, 1, 31),
        ingested_at=ingested_at,
    )
    pipeline.process_active_mobility_sensors(
        config,
        [sensor, sensor_without_coordinates],
        ingested_at=ingested_at,
    )

    counts_root = tmp_path / "silver" / "active_mobility"
    bronze_counts = pl.read_parquet(
        tmp_path
        / "bronze"
        / "active_mobility"
        / "year=2025"
        / "month=01"
        / "active_mobility_counts.parquet"
    )
    silver_counts = pl.read_parquet(
        counts_root
        / "year=2025"
        / "month=01"
        / "active_mobility_counts.parquet"
    )
    bronze_sensors = pl.read_parquet(
        tmp_path
        / "bronze"
        / "active_mobility"
        / "reference"
        / "active_mobility_sensors.parquet"
    )
    silver_sensors = pl.read_parquet(
        counts_root / "reference" / "active_mobility_sensors.parquet"
    )

    assert bronze_counts.schema == ACTIVE_MOBILITY_COUNT_BRONZE_SCHEMA
    assert silver_counts.schema == ACTIVE_MOBILITY_COUNT_SILVER_SCHEMA
    assert bronze_sensors.schema == ACTIVE_MOBILITY_SENSOR_BRONZE_SCHEMA
    assert silver_sensors.schema == ACTIVE_MOBILITY_SENSOR_SILVER_SCHEMA
    assert bronze_sensors["id"].to_list() == ["100", "100048744"]
    assert silver_sensors["sensor_id"].to_list() == ["100"]
    assert silver_counts.item(0, "mobility_count") == 18
