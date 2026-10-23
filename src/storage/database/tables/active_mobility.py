from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    Integer,
    PrimaryKeyConstraint,
    String,
    Table,
)

from storage.database.metadata import metadata

active_mobility_counts = Table(
    "active_mobility_counts",
    metadata,
    Column("sensor_id", String(32), nullable=False),
    Column("flow_id", String(32), nullable=False),
    Column("flow_name", String(255), nullable=True),
    Column("travel_mode", String(32), nullable=False),
    Column("direction", String(8), nullable=False),
    Column("timezone", String(64), nullable=False),
    Column("observed_at_local", DateTime(timezone=False), nullable=False),
    Column("observed_at_utc", DateTime(timezone=True), nullable=False),
    Column("interval_minutes", Integer, nullable=False),
    Column("mobility_count", BigInteger, nullable=True),
    Column("source_status", String(16), nullable=False),
    Column("ingested_at", DateTime(timezone=True), nullable=False),
    PrimaryKeyConstraint(
        "flow_id",
        "observed_at_utc",
        "interval_minutes",
        name="pk_active_mobility_counts",
    ),
    CheckConstraint(
        "travel_mode IN ('bike', 'pedestrian', 'scooter')",
        name="ck_active_mobility_counts_travel_mode",
    ),
    CheckConstraint(
        "direction IN ('in', 'out')",
        name="ck_active_mobility_counts_direction",
    ),
    CheckConstraint(
        "interval_minutes IN (15, 60)",
        name="ck_active_mobility_counts_interval",
    ),
    CheckConstraint(
        "mobility_count IS NULL OR mobility_count >= 0",
        name="ck_active_mobility_counts_count",
    ),
    CheckConstraint(
        "source_status IN ('raw', 'modified', 'deleted')",
        name="ck_active_mobility_counts_status",
    ),
)

active_mobility_sensors = Table(
    "active_mobility_sensors",
    metadata,
    Column("sensor_id", String(32), nullable=False),
    Column("sensor_name", String(255), nullable=False),
    Column("latitude", Float, nullable=False),
    Column("longitude", Float, nullable=False),
    Column("timezone", String(64), nullable=False),
    Column("first_observed_at_local", DateTime(timezone=False), nullable=False),
    Column("last_observed_at_local", DateTime(timezone=False), nullable=False),
    Column("recording_interval_minutes", Integer, nullable=False),
    Column("travel_modes", String(64), nullable=False),
    Column("is_directional", Boolean, nullable=False),
    Column("has_timestamped_data", Boolean, nullable=False),
    Column("has_weather", Boolean, nullable=False),
    Column("operator_name", String(255), nullable=False),
    Column("ingested_at", DateTime(timezone=True), nullable=False),
    PrimaryKeyConstraint("sensor_id", name="pk_active_mobility_sensors"),
    CheckConstraint(
        "latitude BETWEEN -90 AND 90",
        name="ck_active_mobility_sensors_latitude",
    ),
    CheckConstraint(
        "longitude BETWEEN -180 AND 180",
        name="ck_active_mobility_sensors_longitude",
    ),
    CheckConstraint(
        "recording_interval_minutes IN (15, 60)",
        name="ck_active_mobility_sensors_interval",
    ),
)
