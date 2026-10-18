from datetime import date
from unittest.mock import Mock, call

import pytest

import mta_subway_pipeline.backfill as backfill


def test_backfill_subway_processes_each_month(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process_month = Mock()
    monkeypatch.setattr(backfill, "process_subway_month", process_month)

    backfill.backfill_subway(
        {},
        start_date=date(2025, 1, 15),
        end_date=date(2025, 3, 10),
        page_size=1_000,
        app_token="token",
    )

    ingested_at = process_month.call_args_list[0].kwargs["ingested_at"]
    assert process_month.call_args_list == [
        call(
            {},
            date(2025, 1, 15),
            date(2025, 1, 31),
            page_size=1_000,
            app_token="token",
            ingested_at=ingested_at,
        ),
        call(
            {},
            date(2025, 2, 1),
            date(2025, 2, 28),
            page_size=1_000,
            app_token="token",
            ingested_at=ingested_at,
        ),
        call(
            {},
            date(2025, 3, 1),
            date(2025, 3, 10),
            page_size=1_000,
            app_token="token",
            ingested_at=ingested_at,
        ),
    ]
