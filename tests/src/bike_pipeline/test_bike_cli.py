from datetime import date
from pathlib import Path
from unittest.mock import Mock

import pytest

from bike_pipeline import cli


def test_main_runs_backfill_with_default_source_files(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config: dict[str, object] = {}
    backfill_bike = Mock()
    load_bike_range = Mock()
    monkeypatch.setattr(cli, "load_config", Mock(return_value=config))
    monkeypatch.setattr(cli, "backfill_bike", backfill_bike)
    monkeypatch.setattr(cli, "load_bike_range", load_bike_range)

    result = cli.main(
        [
            "backfill",
            "--start-date",
            "2025-01-15",
            "--end-date",
            "2025-03-10",
        ]
    )

    assert result == 0
    backfill_bike.assert_called_once_with(
        config=config,
        counts_file_path=Path("data/raw/bicycle_counts.csv"),
        counters_file_path=Path("data/raw/bicycle_counters.csv"),
        start_date=date(2025, 1, 15),
        end_date=date(2025, 3, 10),
    )
    load_bike_range.assert_not_called()


def test_main_loads_existing_partitions_into_warehouse(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config: dict[str, object] = {}
    backfill_bike = Mock()
    load_bike_range = Mock(return_value=100)
    monkeypatch.setattr(cli, "load_config", Mock(return_value=config))
    monkeypatch.setattr(cli, "backfill_bike", backfill_bike)
    monkeypatch.setattr(cli, "load_bike_range", load_bike_range)

    result = cli.main(
        [
            "warehouse",
            "--start-date",
            "2025-01-01",
            "--end-date",
            "2025-01-31",
        ]
    )

    assert result == 0
    backfill_bike.assert_not_called()
    load_bike_range.assert_called_once_with(
        config=config,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
    )


def test_main_runs_backfill_before_warehouse(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config: dict[str, object] = {}
    calls: list[str] = []
    backfill_bike = Mock(side_effect=lambda **kwargs: calls.append("backfill"))
    load_bike_range = Mock(
        side_effect=lambda **kwargs: calls.append("warehouse")
    )
    monkeypatch.setattr(cli, "load_config", Mock(return_value=config))
    monkeypatch.setattr(cli, "backfill_bike", backfill_bike)
    monkeypatch.setattr(cli, "load_bike_range", load_bike_range)

    result = cli.main(
        [
            "pipeline",
            "--counts-file",
            "custom-counts.csv",
            "--counters-file",
            "custom-counters.csv",
            "--start-date",
            "2025-01-01",
            "--end-date",
            "2025-01-31",
        ]
    )

    assert result == 0
    assert calls == ["backfill", "warehouse"]
    backfill_bike.assert_called_once_with(
        config=config,
        counts_file_path=Path("custom-counts.csv"),
        counters_file_path=Path("custom-counters.csv"),
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
    )
    load_bike_range.assert_called_once_with(
        config=config,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
    )


def test_main_rejects_invalid_date() -> None:
    with pytest.raises(SystemExit, match="2"):
        cli.main(
            [
                "pipeline",
                "--start-date",
                "01-01-2025",
                "--end-date",
                "2025-01-31",
            ]
        )
