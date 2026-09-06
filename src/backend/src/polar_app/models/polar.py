from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from polar_app.models.base import Base


class PolarRawPayload(Base):
    __tablename__ = "polar_raw_payloads"
    __table_args__ = (UniqueConstraint("endpoint", "external_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(255))
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    training_session: Mapped["PolarTrainingSession | None"] = relationship(
        back_populates="raw_payload"
    )


class PolarTrainingSession(Base):
    __tablename__ = "polar_training_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    sport_type: Mapped[str] = mapped_column(String(255), nullable=False)
    sport_name: Mapped[str | None] = mapped_column(String(255))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    local_date: Mapped[date] = mapped_column(Date, nullable=False)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    distance_meters: Mapped[float | None] = mapped_column(Float)
    average_speed_meters_per_second: Mapped[float | None] = mapped_column(Float)
    average_pace_seconds_per_kilometer: Mapped[float | None] = mapped_column(Float)
    duration_pace_index: Mapped[float | None] = mapped_column(Float)
    average_heart_rate: Mapped[int | None] = mapped_column(Integer)
    maximum_heart_rate: Mapped[int | None] = mapped_column(Integer)
    calories: Mapped[int | None] = mapped_column(Integer)
    training_load: Mapped[float | None] = mapped_column(Float)
    raw_payload_id: Mapped[int] = mapped_column(
        ForeignKey("polar_raw_payloads.id", ondelete="RESTRICT"), nullable=False
    )

    raw_payload: Mapped[PolarRawPayload] = relationship(back_populates="training_session")


class PolarSleepDay(Base):
    __tablename__ = "polar_sleep_days"

    id: Mapped[int] = mapped_column(primary_key=True)
    sleep_date: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    score: Mapped[int | None] = mapped_column(Integer)
    raw_payload_id: Mapped[int] = mapped_column(
        ForeignKey("polar_raw_payloads.id", ondelete="RESTRICT"), nullable=False
    )


class PolarNightlyRecharge(Base):
    __tablename__ = "polar_nightly_recharge"

    id: Mapped[int] = mapped_column(primary_key=True)
    recharge_date: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
    status: Mapped[str | None] = mapped_column(String(100))
    ans_charge: Mapped[float | None] = mapped_column(Float)
    ans_charge_status: Mapped[int | None] = mapped_column(Integer)
    nightly_recharge_status: Mapped[int | None] = mapped_column(Integer)
    nightly_heart_rate_avg: Mapped[int | None] = mapped_column(Integer)
    heart_rate_variability_avg: Mapped[int | None] = mapped_column(Integer)
    breathing_rate_avg: Mapped[float | None] = mapped_column(Float)
    raw_payload_id: Mapped[int] = mapped_column(
        ForeignKey("polar_raw_payloads.id", ondelete="RESTRICT"), nullable=False
    )


class PolarActivityDay(Base):
    __tablename__ = "polar_activity_days"

    id: Mapped[int] = mapped_column(primary_key=True)
    activity_date: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
    active_steps: Mapped[int | None] = mapped_column(Integer)
    active_calories: Mapped[int | None] = mapped_column(Integer)
    raw_payload_id: Mapped[int] = mapped_column(
        ForeignKey("polar_raw_payloads.id", ondelete="RESTRICT"), nullable=False
    )


class PolarHeartRateSample(Base):
    __tablename__ = "polar_heart_rate_samples"
    __table_args__ = (UniqueConstraint("sampled_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    sampled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    heart_rate: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_payload_id: Mapped[int] = mapped_column(
        ForeignKey("polar_raw_payloads.id", ondelete="RESTRICT"), nullable=False
    )


class PolarOAuthToken(Base):
    __tablename__ = "polar_oauth_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    polar_user_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    encrypted_access_token: Mapped[str] = mapped_column(Text, nullable=False)
    token_type: Mapped[str] = mapped_column(String(50), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
