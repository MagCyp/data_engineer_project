from datetime import date
from pathlib import Path
from unittest.mock import Mock, call

import pytest

import mta_subway_pipeline.warehouse as warehouse


def test_load_subway_range_loads_each_month_and_returns_total(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = [tmp_path / "january.parquet", tmp_path / "february.parquet"]
    for path in paths:
        path.touch()
    get_path = Mock(side_effect=paths)
    load_subway = Mock(side_effect=[10, 20])
    monkeypatch.setattr(warehouse, "get_subway_ridership_path", get_path)
    monkeypatch.setattr(warehouse, "load_subway", load_subway)

    loaded_rows = warehouse.load_subway_range(
        {},
        date(2025, 1, 15),
        date(2025, 2, 10),
    )

    assert loaded_rows == 30
    assert get_path.call_args_list == [
        call({}, year=2025, month=1, storage_key="silver_path"),
        call({}, year=2025, month=2, storage_key="silver_path"),
    ]
    assert load_subway.call_args_list == [call(paths[0]), call(paths[1])]


def test_load_subway_range_rejects_missing_partition(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    load_subway = Mock()
    monkeypatch.setattr(
        warehouse,
        "get_subway_ridership_path",
        Mock(return_value=tmp_path / "missing.parquet"),
    )
    monkeypatch.setattr(warehouse, "load_subway", load_subway)

    with pytest.raises(FileNotFoundError, match="Silver subway partition"):
        warehouse.load_subway_range(
            {},
            date(2025, 1, 1),
            date(2025, 1, 31),
        )

    load_subway.assert_not_called()
