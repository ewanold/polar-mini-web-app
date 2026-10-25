"""Store Polar daily cardio load components."""

import sqlalchemy as sa

from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "polar_cardio_load",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("load_date", sa.Date(), nullable=False, unique=True),
        sa.Column("strain", sa.Float(), nullable=True),
        sa.Column("tolerance", sa.Float(), nullable=True),
        sa.Column(
            "raw_payload_id", sa.Integer(), sa.ForeignKey("polar_raw_payloads.id"), nullable=False
        ),
    )


def downgrade() -> None:
    op.drop_table("polar_cardio_load")
