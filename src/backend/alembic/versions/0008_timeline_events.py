"""add timeline events

Revision ID: 0008
Revises: 0007
Create Date: 2026-09-05
"""

from alembic import op
import sqlalchemy as sa

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "timeline_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_timeline_events_event_date", "timeline_events", ["event_date"])


def downgrade() -> None:
    op.drop_index("ix_timeline_events_event_date", table_name="timeline_events")
    op.drop_table("timeline_events")
