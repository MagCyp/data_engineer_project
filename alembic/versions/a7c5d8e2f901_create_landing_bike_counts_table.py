"""create landing bike counts table

Revision ID: a7c5d8e2f901
Revises: 04cb76f30f7b
Create Date: 2026-10-15

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a7c5d8e2f901"
down_revision: str | Sequence[str] | None = "04cb76f30f7b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the landing table for normalized bike counts."""
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


def downgrade() -> None:
    """Drop the landing bike-count table."""
    op.drop_table("bike_counts", schema="landing")
