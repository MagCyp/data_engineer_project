from datetime import UTC, datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from bike_pipeline.validation.models import BikeObservation, BikeSourceRecord


def test_bike_source_record_parses_source_datetime() -> None:
    record = BikeSourceRecord.model_validate(
        {
            "countid": "19831896",
            "id": "100009425",
            "date": "06/03/2023 12:15:00 AM",
            "counts": "1,009",
            "status": "0",
        }
    )

    assert record.date == datetime(2023, 6, 3, 0, 15)
    assert record.counts == 1009


@pytest.mark.parametrize(
    ("field", "value"),
    [("countid", 0), ("id", -1), ("counts", -1)],
)
def test_bike_source_record_rejects_invalid_values(
    field: str,
    value: int,
) -> None:
    payload = {
        "countid": 19831896,
        "id": 100009425,
        "date": "06/03/2023 12:15:00 AM",
        "counts": 9,
        "status": 0,
    }
    payload[field] = value

    with pytest.raises(ValidationError):
        BikeSourceRecord.model_validate(payload)


def test_bike_observation_normalizes_ingested_at_to_utc() -> None:
    observation = BikeObservation(
        record_id=19831896,
        counter_id=100009425,
        timezone="America/New_York",
        observed_at_local=datetime(2023, 6, 3, 0, 15),
        observed_at_utc=datetime(2023, 6, 3, 4, 15, tzinfo=UTC),
        bike_count=9,
        status=0,
        ingested_at=datetime(
            2026,
            10,
            15,
            14,
            0,
            tzinfo=timezone(timedelta(hours=2)),
        ),
    )

    assert observation.ingested_at == datetime(2026, 10, 15, 12, 0, tzinfo=UTC)


def test_bike_observation_rejects_timezone_on_local_timestamp() -> None:
    with pytest.raises(ValidationError, match="must not contain a timezone"):
        BikeObservation(
            record_id=19831896,
            counter_id=100009425,
            timezone="America/New_York",
            observed_at_local=datetime(2023, 6, 3, tzinfo=UTC),
            observed_at_utc=datetime(2023, 6, 3, 4, 0, tzinfo=UTC),
            bike_count=9,
            status=0,
            ingested_at=datetime(2026, 10, 15, 12, 0, tzinfo=UTC),
        )
