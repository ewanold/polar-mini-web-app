"""Add distance-to-pace training indices.

Revision ID: 0009
Revises: 0008
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("polar_training_sessions") as batch:
        batch.add_column(sa.Column("distance_pace_index", sa.Float(), nullable=True))
    with op.batch_alter_table("training_aggregates") as batch:
        batch.add_column(sa.Column("average_distance_pace_index", sa.Float(), nullable=True))
        batch.add_column(
            sa.Column(
                "average_distance_pace_index_sample_count",
                sa.Integer(),
                nullable=False,
                server_default="0",
            )
        )
    op.execute(
        "UPDATE polar_training_sessions SET distance_pace_index = "
        "distance_meters / 1000.0 / average_pace_seconds_per_kilometer "
        "WHERE distance_meters IS NOT NULL AND average_pace_seconds_per_kilometer > 0"
    )
    op.execute(
        "UPDATE training_aggregates SET average_distance_pace_index = ("
        "SELECT AVG(session.distance_pace_index) FROM polar_training_sessions AS session "
        "JOIN polar_sport_type_mappings AS mapping ON mapping.sport_type = session.sport_type "
        "WHERE mapping.group_id = training_aggregates.group_id AND mapping.state = 'mapped' "
        "AND session.local_date >= training_aggregates.bucket_start "
        "AND session.local_date < training_aggregates.bucket_end)"
    )
    op.execute(
        "UPDATE training_aggregates SET average_distance_pace_index_sample_count = ("
        "SELECT COUNT(session.distance_pace_index) FROM polar_training_sessions AS session "
        "JOIN polar_sport_type_mappings AS mapping ON mapping.sport_type = session.sport_type "
        "WHERE mapping.group_id = training_aggregates.group_id AND mapping.state = 'mapped' "
        "AND session.local_date >= training_aggregates.bucket_start "
        "AND session.local_date < training_aggregates.bucket_end)"
    )


def downgrade() -> None:
    with op.batch_alter_table("training_aggregates") as batch:
        batch.drop_column("average_distance_pace_index_sample_count")
        batch.drop_column("average_distance_pace_index")
    with op.batch_alter_table("polar_training_sessions") as batch:
        batch.drop_column("distance_pace_index")