from pathlib import Path

from storage.datasets.subway import (
    SUBWAY_PIPELINE_NAME,
    get_subway_ridership_path,
)


def test_get_subway_ridership_path_uses_month_partition(
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
            )
        }
    }

    result = get_subway_ridership_path(config, year=2025, month=1)

    assert result == (
        tmp_path
        / "bronze"
        / SUBWAY_PIPELINE_NAME
        / "year=2025"
        / "month=01"
        / "subway_ridership.parquet"
    )
