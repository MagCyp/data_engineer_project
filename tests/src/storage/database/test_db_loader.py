from datetime import UTC, datetime
from unittest.mock import MagicMock

import polars as pl
import pytest
from sqlalchemy import Connection
from sqlalchemy.dialects import postgresql

from storage.database.db_loader import (
    copy_into_database,
    save_into_stage,
    upsert_dataframe,
)
from storage.database.tables import weather_observations


def silver_dataframe() -> pl.DataFrame:
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
        }
    )


def test_save_into_stage_creates_temporary_table_and_uses_copy() -> None:
    connection = MagicMock(spec=Connection)
    driver_connection = connection.connection.driver_connection
    cursor = driver_connection.cursor.return_value.__enter__.return_value
    copy = cursor.copy.return_value.__enter__.return_value
    data = silver_dataframe()

    stage_table = save_into_stage(data, connection, weather_observations)

    assert stage_table.name.startswith("stage_weather_observations_")
    assert len(stage_table.name) <= 63
    assert list(stage_table.columns.keys()) == list(data.columns)
    assert "TEMPORARY" in stage_table._prefixes
    assert stage_table.dialect_options["postgresql"]["on_commit"] == "DROP"
    copy_statement = cursor.copy.call_args.args[0]
    assert copy_statement.as_string() == (
        f'COPY "{stage_table.name}" '
        '("location", "timezone", "observed_at_utc", "temperature_c", '
        '"relative_humidity_pct", "precipitation_mm", "rain_mm", '
        '"wind_speed_kmh", "ingested_at") FROM STDIN'
    )
    copy.write_row.assert_called_once_with(next(data.iter_rows()))
    connection.execute.assert_not_called()


def test_save_into_stage_rejects_wrong_columns() -> None:
    connection = MagicMock(spec=Connection)
    data = silver_dataframe().drop("rain_mm")

    with pytest.raises(ValueError, match="missing: rain_mm"):
        save_into_stage(data, connection, weather_observations)


def test_copy_into_database_builds_primary_key_upsert() -> None:
    connection = MagicMock(spec=Connection)
    connection.execute.return_value.rowcount = 1
    stage_table = save_into_stage(
        silver_dataframe().clear(),
        connection,
        weather_observations,
    )
    connection.reset_mock()

    inserted_rows = copy_into_database(
        connection,
        stage_table,
        weather_observations,
    )

    statement = connection.execute.call_args.args[0]
    sql = str(statement.compile(dialect=postgresql.dialect()))
    assert inserted_rows == 1
    assert statement.get_execution_options()["preserve_rowcount"] is True
    assert "INSERT INTO landing.weather_observations" in sql
    assert "ON CONFLICT (location, observed_at_utc) DO UPDATE" in sql
    assert "temperature_c = excluded.temperature_c" in sql


def test_upsert_dataframe_runs_staging_and_copy() -> None:
    connection = MagicMock(spec=Connection)
    connection.execute.return_value.rowcount = 1

    inserted_rows = upsert_dataframe(
        silver_dataframe(),
        connection,
        weather_observations,
    )

    assert inserted_rows == 1
    assert connection.execute.call_count == 1
    copy = (
        connection.connection.driver_connection.cursor.return_value
        .__enter__.return_value.copy.return_value.__enter__.return_value
    )
    copy.write_row.assert_called_once()
