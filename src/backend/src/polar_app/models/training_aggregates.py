from datetime import date
from typing import Literal

from sqlalchemy import Date, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from polar_app.models.base import Base

AggregationResolution = Literal["day", "week", "month"]


class TrainingAggregate(Base):
    """A rebuildable per-group cache derived directly from normalized sessions."""

    __tablename__ = "training_aggregates"
    __table_args__ = (
        UniqueConstraint("group_id", "resolution", "bucket_start", "timezone"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("training_groups.id", ondelete="CASCADE"), nullable=False
    )
    resolution: Mapped[AggregationResolution] = mapped_column(String(10), nullable=False)
    bucket_start: Mapped[date] = mapped_column(Date, nullable=False)
    bucket_end: Mapped[date] = mapped_column(Date, nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    aggregation_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    session_count: Mapped[int] = mapped_column(Integer, nullable=False)
    total_distance_meters: Mapped[float | None] = mapped_column(Float)
    average_heart_rate: Mapped[float | None] = mapped_column(Float)
    average_heart_rate_sample_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    average_pace_seconds_per_kilometer: Mapped[float | None] = mapped_column(Float)
    average_pace_sample_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    average_duration_seconds: Mapped[float | None] = mapped_column(Float)
    average_duration_sample_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    average_duration_pace_index: Mapped[float | None] = mapped_column(Float)
    average_duration_pace_index_sample_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
