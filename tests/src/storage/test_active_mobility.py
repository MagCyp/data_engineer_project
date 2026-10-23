from pathlib import Path

from storage.datasets.active_mobility import (
    ACTIVE_MOBILITY_PIPELINE_NAME,
    get_active_mobility_counts_path,
    get_active_mobility_sensors_path,
)


def test_active_mobility_paths_use_pipeline_storage(tmp_path: Path) -> None:
    config = {
        "storage": {
            "bronze_path": str(
                tmp_path
                / "bronze"
                / "{pipeline_name}"
                / "year={year}"
                / "month={month}"
            ),
            "bronze_reference_path": str(
                tmp_path / "bronze" / "{pipeline_name}" / "reference"
            ),
        }
    }

    assert get_active_mobility_counts_path(
        config,
        year=2025,
        month=1,
    ) == (
        tmp_path
        / "bronze"
        / ACTIVE_MOBILITY_PIPELINE_NAME
        / "year=2025"
        / "month=01"
        / "active_mobility_counts.parquet"
    )
    assert get_active_mobility_sensors_path(config) == (
        tmp_path
        / "bronze"
        / ACTIVE_MOBILITY_PIPELINE_NAME
        / "reference"
        / "active_mobility_sensors.parquet"
    )
