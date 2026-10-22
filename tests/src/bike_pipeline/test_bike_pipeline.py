from datetime import UTC, date, datetime
from pathlib import Path

import polars as pl

from bike_pipeline.pipeline import process_bike_month


def test_process_bike_month_writes_bronze_and_silver(
    tmp_path: Path,
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
    source = pl.DataFrame(
        {
            "countid": [1, 2],
            "id": [101, 101],
            "date": [
                datetime(2023, 6, 3, 0, 0),
                datetime(2023, 7, 3, 0, 0),
            ],
            "counts": [27, 9],
            "status": [0, 0],
        }
    )
    counters = pl.DataFrame(
        {
            "id": [101],
            "timezone": ["(UTC-05:00) US/Eastern;DST"],
        }
    )

    process_bike_month(
        config,
        source,
        counters,
        date(2023, 6, 1),
        date(2023, 6, 30),
        ingested_at=datetime(2026, 10, 15, 12, 0, tzinfo=UTC),
    )

    bronze = pl.read_parquet(
        tmp_path
        / "bronze"
        / "bike"
        / "year=2023"
        / "month=06"
        / "bike_counts.parquet"
    )
    silver = pl.read_parquet(
        tmp_path
        / "silver"
        / "bike"
        / "year=2023"
        / "month=06"
        / "bike_counts.parquet"
    )
    assert bronze["countid"].to_list() == [1]
    assert silver["record_id"].to_list() == [1]
    assert silver.item(0, "observed_at_utc") == datetime(
        2023,
        6,
        3,
        4,
        0,
        tzinfo=UTC,
    )


def test_process_bike_month_merges_partial_month_runs(tmp_path: Path) -> None:
    config = {
        "storage": {
            "bronze_path": str(
                tmp_path / "bronze" / "{pipeline_name}"
                / "year={year}" / "month={month}"
            ),
            "silver_path": str(
                tmp_path / "silver" / "{pipeline_name}"
                / "year={year}" / "month={month}"
            ),
        }
    }
    source = pl.DataFrame(
        {
            "countid": [1, 2],
            "id": [101, 101],
            "date": [datetime(2023, 6, 3), datetime(2023, 6, 4)],
            "counts": [27, 9],
            "status": [0, 0],
        }
    )
    counters = pl.DataFrame(
        {
            "id": [101],
            "timezone": ["(UTC-05:00) US/Eastern;DST"],
        }
    )

    process_bike_month(
        config,
        source,
        counters,
        date(2023, 6, 3),
        date(2023, 6, 3),
        ingested_at=datetime(2026, 10, 15, 12, tzinfo=UTC),
    )
    process_bike_month(
        config,
        source,
        counters,
        date(2023, 6, 4),
        date(2023, 6, 4),
        ingested_at=datetime(2026, 10, 16, 12, tzinfo=UTC),
    )

    partition = (
        tmp_path / "silver" / "bike" / "year=2023" / "month=06"
        / "bike_counts.parquet"
    )
    result = pl.read_parquet(partition).sort("record_id")
    assert result["record_id"].to_list() == [1, 2]
    assert result["bike_count"].to_list() == [27, 9]

    process_bike_month(
        config,
        source,
        counters,
        date(2023, 6, 4),
        date(2023, 6, 4),
        ingested_at=datetime(2026, 10, 17, 12, tzinfo=UTC),
    )

    rerun = pl.read_parquet(partition).sort("record_id")
    assert rerun.height == 2
    assert rerun.item(1, "ingested_at") == datetime(
        2026,
        10,
        17,
        12,
        tzinfo=UTC,
    )
