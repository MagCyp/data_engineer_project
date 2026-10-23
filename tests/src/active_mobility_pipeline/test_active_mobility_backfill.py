from datetime import date
from unittest.mock import Mock, call

import pytest

import active_mobility_pipeline.backfill as backfill


def test_backfill_fetches_sensors_once_and_processes_each_month(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sensors = [Mock()]
    fetch_sensors = Mock(return_value=sensors)
    process_sensors = Mock()
    process_month = Mock()
    monkeypatch.setattr(backfill, "fetch_sensor_records", fetch_sensors)
    monkeypatch.setattr(
        backfill,
        "process_active_mobility_sensors",
        process_sensors,
    )
    monkeypatch.setattr(
        backfill,
        "process_active_mobility_month",
        process_month,
    )

    backfill.backfill_active_mobility(
        {},
        start_date=date(2025, 1, 15),
        end_date=date(2025, 2, 10),
        page_size=100,
        app_token="token",
    )

    ingested_at = process_sensors.call_args.kwargs["ingested_at"]
    fetch_sensors.assert_called_once_with(
        {},
        page_size=100,
        app_token="token",
    )
    process_sensors.assert_called_once_with(
        {},
        sensors,
        ingested_at=ingested_at,
    )
    assert process_month.call_args_list == [
        call(
            {},
            date(2025, 1, 15),
            date(2025, 1, 31),
            page_size=100,
            app_token="token",
            ingested_at=ingested_at,
        ),
        call(
            {},
            date(2025, 2, 1),
            date(2025, 2, 10),
            page_size=100,
            app_token="token",
            ingested_at=ingested_at,
        ),
    ]
