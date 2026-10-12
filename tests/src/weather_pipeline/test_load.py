from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock

import polars as pl
import pytest
from sqlalchemy import Engine

import weather_pipeline.load as weather_load
from storage.database.tables import weather_observations
from weather_pipeline.load import SILVER_WEATHER_SCHEMA, load_weather


def silver_weather_dataframe() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "location": ["New York"],
            "timezone": ["GMT"],
            "observed_at_utc": [datetime(2025, 1, 1, tzinfo=UTC)],
            "temperature_c": [3.2],
            "relative_humidity_pct": [72],
            "precipitation_mm": [0.0],
            "rain_mm": [0.0],
            "wind_speed_kmh": [8.1],
            "ingested_at": [datetime(2026, 10, 12, tzinfo=UTC)],
        },
        schema=SILVER_WEATHER_SCHEMA,
    )


def test_load_weather_validates_and_upserts_silver_parquet(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    file_path = tmp_path / "weather_observations.parquet"
    dataframe = silver_weather_dataframe()
    dataframe.write_parquet(file_path)
    engine = MagicMock(spec=Engine)
    connection = engine.begin.return_value.__enter__.return_value
    upsert_dataframe = MagicMock(return_value=1)
    monkeypatch.setattr(weather_load, "get_engine", MagicMock(return_value=engine))
    monkeypatch.setattr(weather_load, "upsert_dataframe", upsert_dataframe)

    loaded_rows = load_weather(file_path)

    assert loaded_rows == 1
    loaded_dataframe, used_connection, target_table = (
        upsert_dataframe.call_args.args
    )
    assert loaded_dataframe.equals(dataframe)
    assert used_connection is connection
    assert target_table is weather_observations
    engine.begin.assert_called_once_with()
    engine.dispose.assert_called_once_with()


def test_load_weather_does_not_open_database_for_invalid_schema(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    file_path = tmp_path / "weather_observations.parquet"
    silver_weather_dataframe().drop("rain_mm").write_parquet(file_path)
    get_engine = MagicMock()
    monkeypatch.setattr(weather_load, "get_engine", get_engine)

    with pytest.raises(ValueError, match="does not match"):
        load_weather(file_path)

    get_engine.assert_not_called()


def test_load_weather_rolls_back_transaction_when_upsert_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    file_path = tmp_path / "weather_observations.parquet"
    silver_weather_dataframe().write_parquet(file_path)
    engine = MagicMock(spec=Engine)
    error = RuntimeError("database write failed")
    monkeypatch.setattr(weather_load, "get_engine", MagicMock(return_value=engine))
    monkeypatch.setattr(
        weather_load,
        "upsert_dataframe",
        MagicMock(side_effect=error),
    )

    with pytest.raises(RuntimeError, match="database write failed"):
        load_weather(file_path)

    exit_arguments = engine.begin.return_value.__exit__.call_args.args
    assert exit_arguments[0] is RuntimeError
    assert exit_arguments[1] is error
    engine.dispose.assert_called_once_with()
