from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Float,
    PrimaryKeyConstraint,
    String,
    Table,
)

from storage.database.metadata import metadata

subway_ridership = Table(
    "subway_ridership",
    metadata,
    Column("observed_at_local", DateTime(timezone=False), nullable=False),
    Column("observed_at_utc", DateTime(timezone=True), nullable=False),
    Column("timezone", String(64), nullable=False),
    Column("transit_mode", String(64), nullable=False),
    Column("station_complex_id", String(64), nullable=False),
    Column("station_complex", String(255), nullable=False),
    Column("borough", String(64), nullable=False),
    Column("payment_method", String(64), nullable=False),
    Column("fare_class_category", String(255), nullable=False),
    Column("ridership", Float, nullable=False),
    Column("transfers", Float, nullable=False),
    Column("latitude", Float, nullable=False),
    Column("longitude", Float, nullable=False),
    Column("ingested_at", DateTime(timezone=True), nullable=False),
    PrimaryKeyConstraint(
        "observed_at_utc",
        "transit_mode",
        "station_complex_id",
        "payment_method",
        "fare_class_category",
        name="pk_subway_ridership",
    ),
    CheckConstraint("ridership >= 0", name="ck_subway_ridership_count"),
    CheckConstraint("transfers >= 0", name="ck_subway_transfers_count"),
    CheckConstraint(
        "transfers <= ridership",
        name="ck_subway_transfers_not_above_ridership",
    ),
    CheckConstraint(
        "latitude BETWEEN -90 AND 90",
        name="ck_subway_latitude",
    ),
    CheckConstraint(
        "longitude BETWEEN -180 AND 180",
        name="ck_subway_longitude",
    ),
)
