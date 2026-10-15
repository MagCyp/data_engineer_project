from datetime import UTC, datetime

import polars as pl
import pytest

from bike_pipeline.transformations import transform_bronze_to_silver
from bike_pipeline.validation import BIKE_BRONZE_SCHEMA, BIKE_SILVER_SCHEMA

SOURCE_TIMEZONE = "(UTC-05:00) US/Eastern;DST"


def bronze_dataframe(times: list[datetime]) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "countid": list(range(1, len(times) + 1)),
            "id": [101] * len(times),
            "date": times,
            "counts": [9] * len(times),
            "status": [0] * len(times),
            "ingested_at": [
                datetime(2026, 10, 15, 12, 0, tzinfo=UTC)
            ]
            * len(times),
        },
        schema=BIKE_BRONZE_SCHEMA,
    )


def counter_dataframe(timezone: str = SOURCE_TIMEZONE) -> pl.DataFrame:
    return pl.DataFrame({"id": [101], "timezone": [timezone]})


def test_transform_bronze_to_silver_joins_timezone_and_converts_dst() -> None:
    bronze = bronze_dataframe(
        [
            datetime(2023, 6, 3, 12, 0),
            datetime(2023, 12, 3, 12, 0),
        ]
    )

    result = transform_bronze_to_silver(bronze, counter_dataframe())

    assert result.schema == BIKE_SILVER_SCHEMA
    assert result["timezone"].to_list() == [
        "America/New_York",
        "America/New_York",
    ]
    assert result["observed_at_utc"].to_list() == [
        datetime(2023, 6, 3, 16, 0, tzinfo=UTC),
        datetime(2023, 12, 3, 17, 0, tzinfo=UTC),
    ]


def test_transform_bronze_to_silver_uses_explicit_fall_back_policy() -> None:
    bronze = bronze_dataframe([datetime(2023, 11, 5, 1, 30)])

    result = transform_bronze_to_silver(bronze, counter_dataframe())

    assert result.item(0, "observed_at_utc") == datetime(
        2023,
        11,
        5,
        5,
        30,
        tzinfo=UTC,
    )


def test_transform_bronze_to_silver_rejects_nonexistent_local_time() -> None:
    bronze = bronze_dataframe([datetime(2023, 3, 12, 2, 30)])

    with pytest.raises(ValueError, match="do not exist"):
        transform_bronze_to_silver(bronze, counter_dataframe())


def test_transform_bronze_to_silver_requires_counter_metadata() -> None:
    bronze = bronze_dataframe([datetime(2023, 6, 3, 12, 0)])
    counters = pl.DataFrame(
        {"id": [202], "timezone": [SOURCE_TIMEZONE]}
    )

    with pytest.raises(ValueError, match="Missing counter metadata"):
        transform_bronze_to_silver(bronze, counters)
