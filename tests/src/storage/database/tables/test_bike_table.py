from sqlalchemy import BigInteger, DateTime, Integer, String

from storage.database import LANDING_SCHEMA, metadata
from storage.database.tables import bike_counts

EXPECTED_COLUMNS = [
    "record_id",
    "counter_id",
    "timezone",
    "observed_at_local",
    "observed_at_utc",
    "bike_count",
    "status",
    "ingested_at",
]


def test_bike_table_is_registered_in_landing_metadata() -> None:
    assert bike_counts.schema == LANDING_SCHEMA
    assert metadata.tables["landing.bike_counts"] is bike_counts


def test_bike_table_matches_silver_columns() -> None:
    assert list(bike_counts.columns.keys()) == EXPECTED_COLUMNS
    assert all(not column.nullable for column in bike_counts.columns)


def test_bike_table_uses_record_id_primary_key() -> None:
    assert [column.name for column in bike_counts.primary_key.columns] == [
        "record_id"
    ]
    assert bike_counts.primary_key.name == "pk_bike_counts"
    assert bike_counts.c.record_id.autoincrement is False


def test_bike_table_uses_expected_sql_types() -> None:
    columns = bike_counts.c

    assert isinstance(columns.record_id.type, BigInteger)
    assert isinstance(columns.counter_id.type, BigInteger)
    assert isinstance(columns.timezone.type, String)
    assert isinstance(columns.observed_at_local.type, DateTime)
    assert columns.observed_at_local.type.timezone is False
    assert isinstance(columns.observed_at_utc.type, DateTime)
    assert columns.observed_at_utc.type.timezone is True
    assert isinstance(columns.bike_count.type, Integer)
    assert isinstance(columns.status.type, Integer)
    assert isinstance(columns.ingested_at.type, DateTime)
    assert columns.ingested_at.type.timezone is True
