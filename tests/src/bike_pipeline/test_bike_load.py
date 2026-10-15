from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock

import polars as pl
import pytest
from sqlalchemy import Engine

import bike_pipeline.load as bike_load
from bike_pipeline.load import SILVER_BIKE_SCHEMA, load_bike
from storage.database.tables import bike_counts


def silver_bike_dataframe() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "record_id": [1],
            "counter_id": [101],
            "timezone": ["America/New_York"],
            "observed_at_local": [datetime(2023, 6, 3, 0, 15)],
            "observed_at_utc": [
                datetime(2023, 6, 3, 4, 15, tzinfo=UTC)
            ],
            "bike_count": [9],
            "status": [0],
            "ingested_at": [datetime(2026, 10, 15, 12, 0, tzinfo=UTC)],
        },
        schema=SILVER_BIKE_SCHEMA,
    )


def test_load_bike_validates_and_upserts_silver_parquet(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    file_path = tmp_path / "bike_counts.parquet"
    dataframe = silver_bike_dataframe()
    dataframe.write_parquet(file_path)
    engine = MagicMock(spec=Engine)
    connection = engine.begin.return_value.__enter__.return_value
    upsert_dataframe = MagicMock(return_value=1)
    monkeypatch.setattr(bike_load, "get_engine", MagicMock(return_value=engine))
    monkeypatch.setattr(bike_load, "upsert_dataframe", upsert_dataframe)

    loaded_rows = load_bike(file_path)

    assert loaded_rows == 1
    loaded_dataframe, used_connection, target_table = (
        upsert_dataframe.call_args.args
    )
    assert loaded_dataframe.equals(dataframe)
    assert used_connection is connection
    assert target_table is bike_counts
    engine.begin.assert_called_once_with()
    engine.dispose.assert_called_once_with()


def test_load_bike_does_not_open_database_for_invalid_schema(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    file_path = tmp_path / "bike_counts.parquet"
    silver_bike_dataframe().drop("timezone").write_parquet(file_path)
    get_engine = MagicMock()
    monkeypatch.setattr(bike_load, "get_engine", get_engine)

    with pytest.raises(ValueError, match="does not match"):
        load_bike(file_path)

    get_engine.assert_not_called()


def test_load_bike_rolls_back_transaction_when_upsert_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    file_path = tmp_path / "bike_counts.parquet"
    silver_bike_dataframe().write_parquet(file_path)
    engine = MagicMock(spec=Engine)
    error = RuntimeError("database write failed")
    monkeypatch.setattr(bike_load, "get_engine", MagicMock(return_value=engine))
    monkeypatch.setattr(
        bike_load,
        "upsert_dataframe",
        MagicMock(side_effect=error),
    )

    with pytest.raises(RuntimeError, match="database write failed"):
        load_bike(file_path)

    exit_arguments = engine.begin.return_value.__exit__.call_args.args
    assert exit_arguments[0] is RuntimeError
    assert exit_arguments[1] is error
    engine.dispose.assert_called_once_with()
