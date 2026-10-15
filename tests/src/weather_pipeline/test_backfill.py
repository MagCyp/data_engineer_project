from datetime import date
from unittest.mock import Mock, call

import pytest

import weather_pipeline.backfill as backfill


def test_backfill_weather_processes_each_month(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process_weather_month = Mock()
    monkeypatch.setattr(backfill, "process_weather_month", process_weather_month)
    config = {"pipelines": {"weather": {"default_city": "New York"}}}

    backfill.backfill_weather(
        config,
        start_date=date(2025, 1, 15),
        end_date=date(2025, 3, 10),
    )

    assert process_weather_month.call_args_list == [
        call(config, "New York", date(2025, 1, 15), date(2025, 1, 31)),
        call(config, "New York", date(2025, 2, 1), date(2025, 2, 28)),
        call(config, "New York", date(2025, 3, 1), date(2025, 3, 10)),
    ]


def test_backfill_weather_uses_explicit_location(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process_weather_month = Mock()
    monkeypatch.setattr(backfill, "process_weather_month", process_weather_month)
    config = {"pipelines": {"weather": {"default_city": "New York"}}}

    backfill.backfill_weather(
        config,
        "Rome",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
    )

    process_weather_month.assert_called_once_with(
        config,
        "Rome",
        date(2025, 1, 1),
        date(2025, 1, 31),
    )
