"""create landing subway ridership table

Revision ID: c4e82b91d6fa
Revises: a7c5d8e2f901
Create Date: 2026-10-18

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c4e82b91d6fa"
down_revision: str | Sequence[str] | None = "a7c5d8e2f901"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the landing table for normalized subway ridership."""
    op.create_table(
        "subway_ridership",
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
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("transit_mode", sa.String(length=64), nullable=False),
        sa.Column(
            "station_complex_id",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "station_complex",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column("borough", sa.String(length=64), nullable=False),
        sa.Column(
            "payment_method",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "fare_class_category",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column("ridership", sa.Float(), nullable=False),
        sa.Column("transfers", sa.Float(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.CheckConstraint(
            "latitude BETWEEN -90 AND 90",
            name="ck_subway_latitude",
        ),
        sa.CheckConstraint(
            "longitude BETWEEN -180 AND 180",
            name="ck_subway_longitude",
        ),
        sa.CheckConstraint(
            "ridership >= 0",
            name="ck_subway_ridership_count",
        ),
        sa.CheckConstraint(
            "transfers >= 0",
            name="ck_subway_transfers_count",
        ),
        sa.CheckConstraint(
            "transfers <= ridership",
            name="ck_subway_transfers_not_above_ridership",
        ),
        sa.PrimaryKeyConstraint(
            "observed_at_utc",
            "transit_mode",
            "station_complex_id",
            "payment_method",
            "fare_class_category",
            name="pk_subway_ridership",
        ),
        schema="landing",
    )


def downgrade() -> None:
    """Drop the landing subway-ridership table."""
    op.drop_table("subway_ridership", schema="landing")
