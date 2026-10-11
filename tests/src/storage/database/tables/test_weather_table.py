from sqlalchemy import DateTime, Float, Integer, String

from storage.database import LANDING_SCHEMA, metadata
from storage.database.tables import weather_observations

EXPECTED_COLUMNS = [
    "location",
    "timezone",
    "observed_at_utc",
    "temperature_c",
    "relative_humidity_pct",
    "precipitation_mm",
    "rain_mm",
    "wind_speed_kmh",
    "ingested_at",
]


def test_weather_table_is_registered_in_landing_metadata() -> None:
    assert weather_observations.schema == LANDING_SCHEMA
    assert metadata.tables["landing.weather_observations"] is weather_observations


def test_weather_table_matches_silver_columns() -> None:
    assert list(weather_observations.columns.keys()) == EXPECTED_COLUMNS
    assert all(not column.nullable for column in weather_observations.columns)


def test_weather_table_has_composite_primary_key() -> None:
    assert [
        column.name for column in weather_observations.primary_key.columns
    ] == ["location", "observed_at_utc"]
    assert weather_observations.primary_key.name == "pk_weather_observations"


def test_weather_table_uses_expected_sql_types() -> None:
    columns = weather_observations.c

    assert isinstance(columns.location.type, String)
    assert isinstance(columns.timezone.type, String)
    assert isinstance(columns.observed_at_utc.type, DateTime)
    assert columns.observed_at_utc.type.timezone is True
    assert isinstance(columns.temperature_c.type, Float)
    assert isinstance(columns.relative_humidity_pct.type, Integer)
    assert isinstance(columns.precipitation_mm.type, Float)
    assert isinstance(columns.rain_mm.type, Float)
    assert isinstance(columns.wind_speed_kmh.type, Float)
    assert isinstance(columns.ingested_at.type, DateTime)
    assert columns.ingested_at.type.timezone is True
