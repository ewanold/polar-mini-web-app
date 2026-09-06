"""Add total distance to training aggregate archives.

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("training_aggregates", sa.Column("total_distance_meters", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("training_aggregates", "total_distance_meters")
