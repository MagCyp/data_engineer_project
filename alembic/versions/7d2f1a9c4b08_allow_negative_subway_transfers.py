"""allow negative subway transfer estimates

Revision ID: 7d2f1a9c4b08
Revises: e82f4a1b6c30
Create Date: 2026-10-24

"""
from collections.abc import Sequence

from alembic import op

revision: str = "7d2f1a9c4b08"
down_revision: str | Sequence[str] | None = "e82f4a1b6c30"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        "ck_subway_transfers_count",
        "subway_ridership",
        schema="landing",
        type_="check",
    )


def downgrade() -> None:
    op.create_check_constraint(
        "ck_subway_transfers_count",
        "subway_ridership",
        "transfers >= 0",
        schema="landing",
    )
