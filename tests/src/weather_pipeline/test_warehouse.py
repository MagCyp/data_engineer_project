from datetime import date
from pathlib import Path
from unittest.mock import Mock, call

import pytest

import weather_pipeline.warehouse as warehouse


def test_load_weather_range_loads_each_month_and_returns_total(
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
    load_weather = Mock(side_effect=[10, 20, 5])
    monkeypatch.setattr(warehouse, "get_weather_observations_path", get_path)
    monkeypatch.setattr(warehouse, "load_weather", load_weather)

    loaded_rows = warehouse.load_weather_range(
        config,
        "New York",
        date(2025, 1, 15),
        date(2025, 3, 10),
    )

    assert loaded_rows == 35
    assert get_path.call_args_list == [
        call(
            config,
            location="New York",
            year=2025,
            month=1,
            storage_key="silver_path",
        ),
        call(
            config,
            location="New York",
            year=2025,
            month=2,
            storage_key="silver_path",
        ),
        call(
            config,
            location="New York",
            year=2025,
            month=3,
            storage_key="silver_path",
        ),
    ]
    assert load_weather.call_args_list == [
        call(paths[0]),
        call(paths[1]),
        call(paths[2]),
    ]


def test_load_weather_range_rejects_missing_partition(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    missing_path = tmp_path / "missing.parquet"
    load_weather = Mock()
    monkeypatch.setattr(
        warehouse,
        "get_weather_observations_path",
        Mock(return_value=missing_path),
    )
    monkeypatch.setattr(warehouse, "load_weather", load_weather)

    with pytest.raises(FileNotFoundError, match="Silver weather partition"):
        warehouse.load_weather_range(
            {},
            "New York",
            date(2025, 1, 1),
            date(2025, 1, 31),
        )

    load_weather.assert_not_called()


def test_load_weather_range_rejects_reversed_dates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    load_weather = Mock()
    monkeypatch.setattr(warehouse, "load_weather", load_weather)

    with pytest.raises(
        ValueError,
        match="start_date must be less than or equal to end_date",
    ):
        warehouse.load_weather_range(
            {},
            "New York",
            date(2025, 2, 1),
            date(2025, 1, 1),
        )

    load_weather.assert_not_called()
