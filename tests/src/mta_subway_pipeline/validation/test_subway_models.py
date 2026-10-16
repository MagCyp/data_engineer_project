from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from mta_subway_pipeline.validation.models import SubwaySourceRecord


def make_source_record() -> dict[str, object]:
    return {
        "transit_timestamp": "2025-01-15T08:00:00.000",
        "transit_mode": " subway ",
        "station_complex_id": "158",
        "station_complex": "86 St (C,B)",
        "borough": "Manhattan",
        "payment_method": "omny",
        "fare_class_category": "OMNY - Full Fare",
        "ridership": "451.0",
        "transfers": "26.0",
        "latitude": "40.78587",
        "longitude": "-73.96892",
        "georeference": {
            "type": "Point",
            "coordinates": [-73.96892, 40.78587],
        },
    }


def test_subway_source_record_parses_socrata_payload() -> None:
    record = SubwaySourceRecord.model_validate(make_source_record())

    assert record.transit_timestamp == datetime(2025, 1, 15, 8)
    assert record.transit_mode == "subway"
    assert record.ridership == 451.0
    assert record.transfers == 26.0
    assert record.georeference is not None
    assert record.georeference.coordinates == (-73.96892, 40.78587)


def test_subway_source_record_rejects_timezone_aware_source_timestamp() -> None:
    payload = make_source_record()
    payload["transit_timestamp"] = datetime(2025, 1, 15, 8, tzinfo=UTC)

    with pytest.raises(
        ValidationError,
        match="transit_timestamp must not contain a timezone",
    ):
        SubwaySourceRecord.model_validate(payload)


def test_subway_source_record_rejects_transfers_above_ridership() -> None:
    payload = make_source_record()
    payload["transfers"] = "452.0"

    with pytest.raises(
        ValidationError,
        match="transfers must not exceed ridership",
    ):
        SubwaySourceRecord.model_validate(payload)
