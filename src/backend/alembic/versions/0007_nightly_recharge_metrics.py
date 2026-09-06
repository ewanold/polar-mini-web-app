"""Store Nightly Recharge measurement metrics.

Revision ID: 0007
Revises: 0006
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("polar_nightly_recharge", sa.Column("nightly_recharge_status", sa.Integer()))
    op.add_column("polar_nightly_recharge", sa.Column("nightly_heart_rate_avg", sa.Integer()))
    op.add_column("polar_nightly_recharge", sa.Column("heart_rate_variability_avg", sa.Integer()))
    op.add_column("polar_nightly_recharge", sa.Column("breathing_rate_avg", sa.Float()))


def downgrade() -> None:
    op.drop_column("polar_nightly_recharge", "breathing_rate_avg")
    op.drop_column("polar_nightly_recharge", "heart_rate_variability_avg")
    op.drop_column("polar_nightly_recharge", "nightly_heart_rate_avg")
    op.drop_column("polar_nightly_recharge", "nightly_recharge_status")
