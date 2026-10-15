from datetime import date
from unittest.mock import Mock

import pytest

from weather_pipeline import cli


def test_main_runs_backfill_with_parsed_dates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = {"pipelines": {"weather": {"default_city": "New York"}}}
    load_config = Mock(return_value=config)
    backfill_weather = Mock()
    load_weather_range = Mock()
    monkeypatch.setattr(cli, "load_config", load_config)
    monkeypatch.setattr(cli, "backfill_weather", backfill_weather)
    monkeypatch.setattr(cli, "load_weather_range", load_weather_range)

    exit_code = cli.main(
        [
            "backfill",
            "--location",
            "Rome",
            "--start-date",
            "2025-01-15",
            "--end-date",
            "2025-03-10",
        ]
    )

    assert exit_code == 0
    load_config.assert_called_once_with()
    backfill_weather.assert_called_once_with(
        config=config,
        location="Rome",
        start_date=date(2025, 1, 15),
        end_date=date(2025, 3, 10),
    )
    load_weather_range.assert_not_called()


def test_main_uses_default_location_when_omitted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = {"pipelines": {"weather": {"default_city": "New York"}}}
    backfill_weather = Mock()
    load_weather_range = Mock()
    monkeypatch.setattr(cli, "load_config", Mock(return_value=config))
    monkeypatch.setattr(cli, "backfill_weather", backfill_weather)
    monkeypatch.setattr(cli, "load_weather_range", load_weather_range)

    cli.main(
        [
            "backfill",
            "--start-date",
            "2025-01-01",
            "--end-date",
            "2025-01-31",
        ]
    )

    backfill_weather.assert_called_once_with(
        config=config,
        location="New York",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
    )
    load_weather_range.assert_not_called()


def test_main_loads_existing_partitions_into_warehouse(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = {"pipelines": {"weather": {"default_city": "New York"}}}
    backfill_weather = Mock()
    load_weather_range = Mock(return_value=744)
    monkeypatch.setattr(cli, "load_config", Mock(return_value=config))
    monkeypatch.setattr(cli, "backfill_weather", backfill_weather)
    monkeypatch.setattr(cli, "load_weather_range", load_weather_range)

    exit_code = cli.main(
        [
            "warehouse",
            "--location",
            "Rome",
            "--start-date",
            "2025-01-01",
            "--end-date",
            "2025-01-31",
        ]
    )

    assert exit_code == 0
    backfill_weather.assert_not_called()
    load_weather_range.assert_called_once_with(
        config=config,
        location="Rome",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
    )


def test_main_runs_full_pipeline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = {"pipelines": {"weather": {"default_city": "New York"}}}
    calls: list[str] = []
    backfill_weather = Mock(side_effect=lambda **kwargs: calls.append("backfill"))
    load_weather_range = Mock(
        side_effect=lambda **kwargs: calls.append("warehouse")
    )
    monkeypatch.setattr(cli, "load_config", Mock(return_value=config))
    monkeypatch.setattr(cli, "backfill_weather", backfill_weather)
    monkeypatch.setattr(cli, "load_weather_range", load_weather_range)

    exit_code = cli.main(
        [
            "pipeline",
            "--start-date",
            "2025-01-01",
            "--end-date",
            "2025-01-31",
        ]
    )

    assert exit_code == 0
    assert calls == ["backfill", "warehouse"]
    expected_arguments = {
        "config": config,
        "location": "New York",
        "start_date": date(2025, 1, 1),
        "end_date": date(2025, 1, 31),
    }
    backfill_weather.assert_called_once_with(**expected_arguments)
    load_weather_range.assert_called_once_with(**expected_arguments)


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
