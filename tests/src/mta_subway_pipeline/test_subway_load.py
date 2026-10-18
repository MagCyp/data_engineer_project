from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock

import polars as pl
import pytest
from sqlalchemy import Engine

import storage.database.parquet_loader as parquet_loader
from mta_subway_pipeline.load import load_subway
from mta_subway_pipeline.validation import SUBWAY_SILVER_SCHEMA
from storage.database.tables import subway_ridership


def silver_subway_dataframe() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "observed_at_local": [datetime(2025, 1, 15, 8)],
            "observed_at_utc": [
                datetime(2025, 1, 15, 13, tzinfo=UTC)
            ],
            "timezone": ["America/New_York"],
            "transit_mode": ["subway"],
            "station_complex_id": ["158"],
            "station_complex": ["86 St (C,B)"],
            "borough": ["Manhattan"],
            "payment_method": ["omny"],
            "fare_class_category": ["OMNY - Full Fare"],
            "ridership": [451.0],
            "transfers": [26.0],
            "latitude": [40.78587],
            "longitude": [-73.96892],
            "ingested_at": [datetime(2026, 10, 18, 12, tzinfo=UTC)],
        },
        schema=SUBWAY_SILVER_SCHEMA,
    )


def test_load_subway_validates_and_upserts_silver_parquet(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    file_path = tmp_path / "subway_ridership.parquet"
    dataframe = silver_subway_dataframe()
    dataframe.write_parquet(file_path)
    engine = MagicMock(spec=Engine)
    connection = engine.begin.return_value.__enter__.return_value
    upsert_dataframe = MagicMock(return_value=1)
    monkeypatch.setattr(
        parquet_loader,
        "get_engine",
        MagicMock(return_value=engine),
    )
    monkeypatch.setattr(parquet_loader, "upsert_dataframe", upsert_dataframe)

    loaded_rows = load_subway(file_path)

    assert loaded_rows == 1
    loaded_dataframe, used_connection, target_table = (
        upsert_dataframe.call_args.args
    )
    assert loaded_dataframe.equals(dataframe)
    assert used_connection is connection
    assert target_table is subway_ridership
    engine.dispose.assert_called_once_with()
