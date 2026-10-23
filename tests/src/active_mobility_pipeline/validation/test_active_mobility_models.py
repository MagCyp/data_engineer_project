from datetime import datetime

import pytest
from pydantic import ValidationError

from active_mobility_pipeline.validation import (
    ActiveMobilityCountSourceRecord,
    ActiveMobilitySensorSourceRecord,
)


def test_count_source_record_parses_socrata_values() -> None:
    record = ActiveMobilityCountSourceRecord.model_validate(
        {
            "sensor_id": "100005020",
            "travelmode": "pedestrian",
            "direction": "in",
            "flowid": "101005020",
            "timestamp": "2025-01-15T08:15:00.000",
            "granularity": "PT15M",
            "counts": "18",
            "status": "modified",
        }
    )

    assert record.timestamp == datetime(2025, 1, 15, 8, 15)
    assert record.counts == 18
    assert record.flowname is None


def test_count_source_record_rejects_misaligned_timestamp() -> None:
    with pytest.raises(ValidationError, match="align with granularity"):
        ActiveMobilityCountSourceRecord.model_validate(
            {
                "sensor_id": "1",
                "travelmode": "bike",
                "direction": "out",
                "flowid": "2",
                "timestamp": "2025-01-15T08:10:00.000",
                "granularity": "PT15M",
                "counts": "1",
                "status": "raw",
            }
        )


def test_sensor_source_record_normalizes_travel_modes() -> None:
    sensor = ActiveMobilitySensorSourceRecord.model_validate(
        {
            "id": "100",
            "name": "Shared Counter",
            "lat": "40.7",
            "lon": "-73.9",
            "firstdata": "2022-09-02T11:15:00.000",
            "lastdata": "2026-10-22T01:15:00.000",
            "granularity": "PT15M",
            "travelmodes": "bike,pedestrian",
            "directional": True,
            "hastimestampeddata": False,
            "hasweather": True,
            "domain_name": "New York City DOT",
        }
    )

    assert sensor.travelmodes == "bike, pedestrian"


def test_sensor_source_record_accepts_missing_coordinate_pair() -> None:
    sensor = ActiveMobilitySensorSourceRecord.model_validate(
        {
            "id": "100048744",
            "name": "Manhattan Bridge Interference Calibration 2018 Bike Counter",
            "firstdata": "2013-07-25T00:00:00.000",
            "lastdata": "2017-05-11T23:45:00.000",
            "granularity": "PT15M",
            "travelmodes": "bike",
            "directional": True,
            "hastimestampeddata": False,
            "hasweather": False,
            "domain_name": "New York City DOT",
        }
    )

    assert sensor.lat is None
    assert sensor.lon is None


def test_sensor_source_record_rejects_partial_coordinate_pair() -> None:
    with pytest.raises(ValidationError, match="both be set or both be null"):
        ActiveMobilitySensorSourceRecord.model_validate(
            {
                "id": "100",
                "name": "Incomplete Counter",
                "lat": "40.7",
                "firstdata": "2025-01-01T00:00:00.000",
                "lastdata": "2025-01-01T00:15:00.000",
                "granularity": "PT15M",
                "travelmodes": "bike",
                "directional": True,
                "hastimestampeddata": False,
                "hasweather": False,
                "domain_name": "New York City DOT",
            }
        )
