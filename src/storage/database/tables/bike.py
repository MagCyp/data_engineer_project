from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    DateTime,
    Integer,
    PrimaryKeyConstraint,
    String,
    Table,
)

from storage.database.metadata import metadata

bike_counts = Table(
    "bike_counts",
    metadata,
    Column("record_id", BigInteger, nullable=False, autoincrement=False),
    Column("counter_id", BigInteger, nullable=False),
    Column("timezone", String(64), nullable=False),
    Column("observed_at_local", DateTime(timezone=False), nullable=False),
    Column("observed_at_utc", DateTime(timezone=True), nullable=False),
    Column("bike_count", Integer, nullable=False),
    Column("status", Integer, nullable=False),
    Column("ingested_at", DateTime(timezone=True), nullable=False),
    PrimaryKeyConstraint("record_id", name="pk_bike_counts"),
    CheckConstraint("record_id > 0", name="ck_bike_counts_record_id"),
    CheckConstraint("counter_id > 0", name="ck_bike_counts_counter_id"),
    CheckConstraint("bike_count >= 0", name="ck_bike_counts_count"),
    CheckConstraint(
        "status IN (0, 1, 2, 4, 8, 16)",
        name="ck_bike_counts_status",
    ),
)
