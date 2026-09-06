"""Add Polar source-data persistence.

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-02
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "polar_raw_payloads",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("endpoint", sa.String(length=255), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("endpoint", "external_id"),
    )
    op.create_table(
        "polar_sync_state",
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("cursor", sa.String(length=500), nullable=True),
        sa.Column("window_start", sa.String(length=100), nullable=True),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("category"),
    )
    op.create_table(
        "polar_oauth_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("polar_user_id", sa.String(length=255), nullable=False),
        sa.Column("encrypted_access_token", sa.Text(), nullable=False),
        sa.Column("token_type", sa.String(length=50), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("polar_user_id"),
    )
    op.create_table(
        "polar_training_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("sport_type", sa.String(length=255), nullable=False),
        sa.Column("sport_name", sa.String(length=255), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("local_date", sa.Date(), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("distance_meters", sa.Float(), nullable=True),
        sa.Column("average_speed_meters_per_second", sa.Float(), nullable=True),
        sa.Column("average_pace_seconds_per_kilometer", sa.Float(), nullable=True),
        sa.Column("average_heart_rate", sa.Integer(), nullable=True),
        sa.Column("maximum_heart_rate", sa.Integer(), nullable=True),
        sa.Column("calories", sa.Integer(), nullable=True),
        sa.Column("training_load", sa.Float(), nullable=True),
        sa.Column("raw_payload_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["raw_payload_id"], ["polar_raw_payloads.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_id"),
    )
    op.create_table(
        "polar_sleep_days",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sleep_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("raw_payload_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["raw_payload_id"], ["polar_raw_payloads.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sleep_date"),
    )
    op.create_table(
        "polar_nightly_recharge",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recharge_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=100), nullable=True),
        sa.Column("ans_charge", sa.Integer(), nullable=True),
        sa.Column("ans_charge_status", sa.String(length=100), nullable=True),
        sa.Column("raw_payload_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["raw_payload_id"], ["polar_raw_payloads.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("recharge_date"),
    )
    op.create_table(
        "polar_activity_days",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("activity_date", sa.Date(), nullable=False),
        sa.Column("active_steps", sa.Integer(), nullable=True),
        sa.Column("active_calories", sa.Integer(), nullable=True),
        sa.Column("raw_payload_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["raw_payload_id"], ["polar_raw_payloads.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("activity_date"),
    )
    op.create_table(
        "polar_heart_rate_samples",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sampled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("heart_rate", sa.Integer(), nullable=False),
        sa.Column("raw_payload_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["raw_payload_id"], ["polar_raw_payloads.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sampled_at"),
    )


def downgrade() -> None:
    op.drop_table("polar_heart_rate_samples")
    op.drop_table("polar_activity_days")
    op.drop_table("polar_nightly_recharge")
    op.drop_table("polar_sleep_days")
    op.drop_table("polar_training_sessions")
    op.drop_table("polar_oauth_tokens")
    op.drop_table("polar_sync_state")
    op.drop_table("polar_raw_payloads")
