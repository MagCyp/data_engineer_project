from sqlalchemy import DateTime, Float, String

from storage.database import LANDING_SCHEMA, metadata
from storage.database.tables import subway_ridership


def test_subway_table_matches_silver_contract() -> None:
    assert subway_ridership.schema == LANDING_SCHEMA
    assert metadata.tables["landing.subway_ridership"] is subway_ridership
    assert list(subway_ridership.columns.keys()) == [
        "observed_at_local",
        "observed_at_utc",
        "timezone",
        "transit_mode",
        "station_complex_id",
        "station_complex",
        "borough",
        "payment_method",
        "fare_class_category",
        "ridership",
        "transfers",
        "latitude",
        "longitude",
        "ingested_at",
    ]
    assert all(not column.nullable for column in subway_ridership.columns)


def test_subway_table_uses_grain_as_primary_key() -> None:
    assert [column.name for column in subway_ridership.primary_key.columns] == [
        "observed_at_utc",
        "transit_mode",
        "station_complex_id",
        "payment_method",
        "fare_class_category",
    ]
    assert subway_ridership.primary_key.name == "pk_subway_ridership"


def test_subway_table_uses_expected_sql_types() -> None:
    columns = subway_ridership.c

    assert isinstance(columns.observed_at_local.type, DateTime)
    assert columns.observed_at_local.type.timezone is False
    assert isinstance(columns.observed_at_utc.type, DateTime)
    assert columns.observed_at_utc.type.timezone is True
    assert isinstance(columns.timezone.type, String)
    assert isinstance(columns.ridership.type, Float)
    assert isinstance(columns.transfers.type, Float)
    assert isinstance(columns.ingested_at.type, DateTime)
    assert columns.ingested_at.type.timezone is True
