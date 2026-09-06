"""Add rebuildable training aggregate archives.

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-04
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "training_aggregates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("resolution", sa.String(length=10), nullable=False),
        sa.Column("bucket_start", sa.Date(), nullable=False),
        sa.Column("bucket_end", sa.Date(), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("aggregation_version", sa.Integer(), nullable=False),
        sa.Column("session_count", sa.Integer(), nullable=False),
        sa.Column("average_heart_rate", sa.Float(), nullable=True),
        sa.Column("average_heart_rate_sample_count", sa.Integer(), nullable=False),
        sa.Column("average_pace_seconds_per_kilometer", sa.Float(), nullable=True),
        sa.Column("average_pace_sample_count", sa.Integer(), nullable=False),
        sa.Column("average_duration_seconds", sa.Float(), nullable=True),
        sa.Column("average_duration_sample_count", sa.Integer(), nullable=False),
        sa.Column("average_duration_pace_index", sa.Float(), nullable=True),
        sa.Column("average_duration_pace_index_sample_count", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["training_groups.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("group_id", "resolution", "bucket_start", "timezone"),
    )


def downgrade() -> None:
    op.drop_table("training_aggregates")
