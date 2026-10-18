from datetime import UTC, date, datetime
from pathlib import Path

import polars as pl
import pytest

import mta_subway_pipeline.pipeline as pipeline
from mta_subway_pipeline.validation import (
    SUBWAY_BRONZE_SCHEMA,
    SUBWAY_SILVER_SCHEMA,
    SubwaySourceRecord,
)


def test_process_subway_month_writes_bronze_and_silver(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = {
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
        }
    }
    record = SubwaySourceRecord(
        transit_timestamp=datetime(2025, 1, 15, 8),
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
        georeference=None,
    )
    monkeypatch.setattr(
        pipeline,
        "iter_subway_records",
        lambda *args, **kwargs: iter([record]),
    )

    pipeline.process_subway_month(
        config,
        date(2025, 1, 1),
        date(2025, 1, 31),
        page_size=100,
        app_token="token",
        ingested_at=datetime(2026, 10, 18, 12, tzinfo=UTC),
    )

    bronze = pl.read_parquet(
        tmp_path
        / "bronze"
        / "mta_subway"
        / "year=2025"
        / "month=01"
        / "subway_ridership.parquet"
    )
    silver = pl.read_parquet(
        tmp_path
        / "silver"
        / "mta_subway"
        / "year=2025"
        / "month=01"
        / "subway_ridership.parquet"
    )

    assert bronze.schema == SUBWAY_BRONZE_SCHEMA
    assert silver.schema == SUBWAY_SILVER_SCHEMA
    assert bronze.height == 1
    assert silver.item(0, "observed_at_utc") == datetime(
        2025,
        1,
        15,
        13,
        tzinfo=UTC,
    )


def test_process_subway_month_rejects_multiple_months() -> None:
    with pytest.raises(ValueError, match="same month"):
        pipeline.process_subway_month(
            {},
            date(2025, 1, 1),
            date(2025, 2, 1),
        )
