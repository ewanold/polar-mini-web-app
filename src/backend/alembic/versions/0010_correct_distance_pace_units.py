"""Correct distance-to-pace index units.

Revision ID: 0010
Revises: 0009
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0010"
down_revision: str | Sequence[str] | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "UPDATE polar_training_sessions SET distance_pace_index = "
        "distance_meters / average_pace_seconds_per_kilometer "
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
    op.execute(
        "UPDATE polar_training_sessions SET distance_pace_index = "
        "distance_meters / 1000.0 / average_pace_seconds_per_kilometer "
        "WHERE distance_meters IS NOT NULL AND average_pace_seconds_per_kilometer > 0"
    )