from datetime import date
from pathlib import Path
from unittest.mock import Mock, call

import pytest

import active_mobility_pipeline.warehouse as warehouse


def test_load_range_loads_sensor_snapshot_and_each_month(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config: dict[str, object] = {}
    sensor_path = tmp_path / "sensors.parquet"
    count_paths = [tmp_path / "january.parquet", tmp_path / "february.parquet"]
    for path in [sensor_path, *count_paths]:
        path.touch()
    get_count_path = Mock(side_effect=count_paths)
    load_counts = Mock(side_effect=[10, 20])
    monkeypatch.setattr(
        warehouse,
        "get_active_mobility_sensors_path",
        Mock(return_value=sensor_path),
    )
    monkeypatch.setattr(
        warehouse,
        "get_active_mobility_counts_path",
        get_count_path,
    )
    monkeypatch.setattr(
        warehouse,
        "load_active_mobility_sensors",
        Mock(return_value=3),
    )
    monkeypatch.setattr(
        warehouse,
        "load_active_mobility_counts",
        load_counts,
    )

    loaded_rows = warehouse.load_active_mobility_range(
        config,
        date(2025, 1, 15),
        date(2025, 2, 10),
    )

    assert loaded_rows == 33
    assert get_count_path.call_args_list == [
        call(config, year=2025, month=1, storage_key="silver_path"),
        call(config, year=2025, month=2, storage_key="silver_path"),
    ]
    assert load_counts.call_args_list == [call(count_paths[0]), call(count_paths[1])]


def test_load_range_rejects_missing_month(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sensor_path = tmp_path / "sensors.parquet"
    sensor_path.touch()
    load_counts = Mock()
    monkeypatch.setattr(
        warehouse,
        "get_active_mobility_sensors_path",
        Mock(return_value=sensor_path),
    )
    monkeypatch.setattr(
        warehouse,
        "get_active_mobility_counts_path",
        Mock(return_value=tmp_path / "missing.parquet"),
    )
    monkeypatch.setattr(
        warehouse,
        "load_active_mobility_sensors",
        Mock(return_value=3),
    )
    monkeypatch.setattr(
        warehouse,
        "load_active_mobility_counts",
        load_counts,
    )

    with pytest.raises(FileNotFoundError, match="Silver active mobility"):
        warehouse.load_active_mobility_range(
            {},
            date(2025, 1, 1),
            date(2025, 1, 31),
        )

    load_counts.assert_not_called()
