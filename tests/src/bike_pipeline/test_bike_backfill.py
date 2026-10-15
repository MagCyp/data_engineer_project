from datetime import date
from pathlib import Path
from unittest.mock import Mock

import polars as pl
import pytest

import bike_pipeline.backfill as backfill


def test_backfill_reads_each_source_once_and_reuses_loaded_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_data = pl.DataFrame({"date": []}, schema={"date": pl.Datetime})
    counter_data = pl.DataFrame({"id": []}, schema={"id": pl.Int64})
    read_counts = Mock(return_value=source_data)
    read_counters = Mock(return_value=counter_data)
    process_month = Mock()
    monkeypatch.setattr(backfill, "read_bike_data", read_counts)
    monkeypatch.setattr(backfill, "read_bike_counter_data", read_counters)
    monkeypatch.setattr(backfill, "process_bike_month", process_month)

    backfill.backfill_bike(
        {},
        Path("counts.csv"),
        Path("counters.csv"),
        start_date=date(2025, 1, 15),
        end_date=date(2025, 3, 10),
    )

    read_counts.assert_called_once_with(
        Path("counts.csv"),
        start_date=date(2025, 1, 15),
        end_date=date(2025, 3, 10),
    )
    read_counters.assert_called_once_with(Path("counters.csv"))
    assert process_month.call_count == 3
    for call in process_month.call_args_list:
        assert call.args[1] is source_data
        assert call.args[2] is counter_data
