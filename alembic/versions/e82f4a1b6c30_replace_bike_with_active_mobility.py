"""replace bike counts with active mobility tables

Revision ID: e82f4a1b6c30
Revises: c4e82b91d6fa
Create Date: 2026-10-23

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "e82f4a1b6c30"
down_revision: str | Sequence[str] | None = "c4e82b91d6fa"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "active_mobility_counts",
        sa.Column("sensor_id", sa.String(length=32), nullable=False),
        sa.Column("flow_id", sa.String(length=32), nullable=False),
        sa.Column("flow_name", sa.String(length=255), nullable=True),
        sa.Column("travel_mode", sa.String(length=32), nullable=False),
        sa.Column("direction", sa.String(length=8), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column(
            "observed_at_local",
            sa.DateTime(timezone=False),
            nullable=False,
        ),
        sa.Column(
            "observed_at_utc",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("interval_minutes", sa.Integer(), nullable=False),
        sa.Column("mobility_count", sa.BigInteger(), nullable=True),
        sa.Column("source_status", sa.String(length=16), nullable=False),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.CheckConstraint(
            "travel_mode IN ('bike', 'pedestrian', 'scooter')",
            name="ck_active_mobility_counts_travel_mode",
        ),
        sa.CheckConstraint(
            "direction IN ('in', 'out')",
            name="ck_active_mobility_counts_direction",
        ),
        sa.CheckConstraint(
            "interval_minutes IN (15, 60)",
            name="ck_active_mobility_counts_interval",
        ),
        sa.CheckConstraint(
            "mobility_count IS NULL OR mobility_count >= 0",
            name="ck_active_mobility_counts_count",
        ),
        sa.CheckConstraint(
            "source_status IN ('raw', 'modified', 'deleted')",
            name="ck_active_mobility_counts_status",
        ),
        sa.PrimaryKeyConstraint(
            "flow_id",
            "observed_at_utc",
            "interval_minutes",
            name="pk_active_mobility_counts",
        ),
        schema="landing",
    )
    op.create_table(
        "active_mobility_sensors",
        sa.Column("sensor_id", sa.String(length=32), nullable=False),
        sa.Column("sensor_name", sa.String(length=255), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column(
            "first_observed_at_local",
            sa.DateTime(timezone=False),
            nullable=False,
        ),
        sa.Column(
            "last_observed_at_local",
            sa.DateTime(timezone=False),
            nullable=False,
        ),
        sa.Column(
            "recording_interval_minutes",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column("travel_modes", sa.String(length=64), nullable=False),
        sa.Column("is_directional", sa.Boolean(), nullable=False),
        sa.Column("has_timestamped_data", sa.Boolean(), nullable=False),
        sa.Column("has_weather", sa.Boolean(), nullable=False),
        sa.Column("operator_name", sa.String(length=255), nullable=False),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.CheckConstraint(
            "latitude BETWEEN -90 AND 90",
            name="ck_active_mobility_sensors_latitude",
        ),
        sa.CheckConstraint(
            "longitude BETWEEN -180 AND 180",
            name="ck_active_mobility_sensors_longitude",
        ),
        sa.CheckConstraint(
            "recording_interval_minutes IN (15, 60)",
            name="ck_active_mobility_sensors_interval",
        ),
        sa.PrimaryKeyConstraint(
            "sensor_id",
            name="pk_active_mobility_sensors",
        ),
        schema="landing",
    )
    # dbt staging/intermediate models are PostgreSQL views that depend on the
    # landing table. CASCADE removes those obsolete views together with the
    # source table; dbt will build the new active-mobility graph afterwards.
    op.execute("DROP TABLE landing.bike_counts CASCADE")


def downgrade() -> None:
    op.create_table(
        "bike_counts",
        sa.Column(
            "record_id",
            sa.BigInteger(),
            nullable=False,
            autoincrement=False,
        ),
        sa.Column("counter_id", sa.BigInteger(), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column(
            "observed_at_local",
            sa.DateTime(timezone=False),
            nullable=False,
        ),
        sa.Column(
            "observed_at_utc",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("bike_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.Integer(), nullable=False),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.CheckConstraint(
            "bike_count >= 0",
            name="ck_bike_counts_count",
        ),
        sa.CheckConstraint(
            "counter_id > 0",
            name="ck_bike_counts_counter_id",
        ),
        sa.CheckConstraint(
            "record_id > 0",
            name="ck_bike_counts_record_id",
        ),
        sa.CheckConstraint(
            "status IN (0, 1, 2, 4, 8, 16)",
            name="ck_bike_counts_status",
        ),
        sa.PrimaryKeyConstraint("record_id", name="pk_bike_counts"),
        schema="landing",
    )
    # Keep downgrade usable after dbt has created views over the new tables.
    op.execute("DROP TABLE landing.active_mobility_sensors CASCADE")
    op.execute("DROP TABLE landing.active_mobility_counts CASCADE")
