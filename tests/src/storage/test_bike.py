from pathlib import Path

from storage.datasets.bike import (
    BIKE_PIPELINE_NAME,
    get_bike_counts_path,
)


def test_get_bike_counts_path_uses_month_partition(tmp_path: Path) -> None:
    config = {
        "storage": {
            "bronze_path": str(
                tmp_path
                / "bronze"
                / "{pipeline_name}"
                / "year={year}"
                / "month={month}"
            )
        }
    }

    result = get_bike_counts_path(config, year=2025, month=1)

    assert result == (
        tmp_path
        / "bronze"
        / BIKE_PIPELINE_NAME
        / "year=2025"
        / "month=01"
        / "bike_counts.parquet"
    )
