from datetime import date
from unittest.mock import Mock

import pytest

from weather_pipeline import cli


def test_main_runs_backfill_with_parsed_dates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = {"default_city": "New York"}
    load_config = Mock(return_value=config)
    backfill_weather = Mock()
    monkeypatch.setattr(cli, "load_config", load_config)
    monkeypatch.setattr(cli, "backfill_weather", backfill_weather)

    exit_code = cli.main(
        [
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


def test_main_uses_default_location_when_omitted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = {"default_city": "New York"}
    backfill_weather = Mock()
    monkeypatch.setattr(cli, "load_config", Mock(return_value=config))
    monkeypatch.setattr(cli, "backfill_weather", backfill_weather)

    cli.main(
        [
            "--start-date",
            "2025-01-01",
            "--end-date",
            "2025-01-31",
        ]
    )

    backfill_weather.assert_called_once_with(
        config=config,
        location=None,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
    )


def test_main_rejects_invalid_date() -> None:
    with pytest.raises(SystemExit, match="2"):
        cli.main(
            [
                "--start-date",
                "01-01-2025",
                "--end-date",
                "2025-01-31",
            ]
        )
