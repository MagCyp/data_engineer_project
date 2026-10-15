from datetime import date
from pathlib import Path
from unittest.mock import Mock, call

import pytest

import bike_pipeline.warehouse as warehouse


def test_load_bike_range_loads_each_month_and_returns_total(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = {"storage": {"silver_path": "unused-in-test"}}
    paths = [
        tmp_path / "january.parquet",
        tmp_path / "february.parquet",
        tmp_path / "march.parquet",
    ]
    for path in paths:
        path.touch()
    get_path = Mock(side_effect=paths)
    load_bike = Mock(side_effect=[10, 20, 5])
    monkeypatch.setattr(warehouse, "get_bike_counts_path", get_path)
    monkeypatch.setattr(warehouse, "load_bike", load_bike)

    loaded_rows = warehouse.load_bike_range(
        config,
        date(2025, 1, 15),
        date(2025, 3, 10),
    )

    assert loaded_rows == 35
    assert get_path.call_args_list == [
        call(config, year=2025, month=1, storage_key="silver_path"),
        call(config, year=2025, month=2, storage_key="silver_path"),
        call(config, year=2025, month=3, storage_key="silver_path"),
    ]
    assert load_bike.call_args_list == [
        call(paths[0]),
        call(paths[1]),
        call(paths[2]),
    ]


def test_load_bike_range_rejects_missing_partition(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    load_bike = Mock()
    monkeypatch.setattr(
        warehouse,
        "get_bike_counts_path",
        Mock(return_value=tmp_path / "missing.parquet"),
    )
    monkeypatch.setattr(warehouse, "load_bike", load_bike)

    with pytest.raises(FileNotFoundError, match="Silver bike partition"):
        warehouse.load_bike_range(
            {},
            date(2025, 1, 1),
            date(2025, 1, 31),
        )

    load_bike.assert_not_called()


def test_load_bike_range_rejects_reversed_dates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    load_bike = Mock()
    monkeypatch.setattr(warehouse, "load_bike", load_bike)

    with pytest.raises(ValueError, match="start_date must be"):
        warehouse.load_bike_range(
            {},
            date(2025, 2, 1),
            date(2025, 1, 1),
        )

    load_bike.assert_not_called()
