from pathlib import Path

from storage.datasets.bike import (
    BIKE_PIPELINE_NAME,
    get_bike_counts_path,
    get_bike_raw_counters_path,
    get_bike_raw_counts_path,
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


def test_get_bike_raw_paths_use_configured_pipeline_directory(
    tmp_path: Path,
) -> None:
    config = {
        "pipelines": {
            "bike": {
                "raw_files": {
                    "counts": "custom_counts.csv",
                    "counters": "custom_counters.csv",
                }
            }
        },
        "storage": {
            "raw_path": str(tmp_path / "raw" / "{pipeline_name}"),
        }
    }

    assert get_bike_raw_counts_path(config) == (
        tmp_path / "raw" / BIKE_PIPELINE_NAME / "custom_counts.csv"
    )
    assert get_bike_raw_counters_path(config) == (
        tmp_path / "raw" / BIKE_PIPELINE_NAME / "custom_counters.csv"
    )
