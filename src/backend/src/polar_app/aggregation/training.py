from collections.abc import Iterable

from polar_app.aggregation.buckets import Bucket
from polar_app.models.polar import PolarTrainingSession
from polar_app.models.training_aggregates import AggregationResolution, TrainingAggregate


def calculate_training_aggregate(
    *,
    group_id: int,
    resolution: AggregationResolution,
    bucket: Bucket,
    timezone: str,
    sessions: Iterable[PolarTrainingSession],
    aggregation_version: int = 1,
) -> TrainingAggregate | None:
    """Calculate one bucket from sessions, omitting it when no sessions contribute."""
    bucket_sessions = [
        session for session in sessions if bucket.start <= session.local_date < bucket.end
    ]
    if not bucket_sessions:
        return None

    average_heart_rate, average_heart_rate_sample_count = average_with_sample_count(
        session.average_heart_rate for session in bucket_sessions
    )
    average_pace, average_pace_sample_count = average_with_sample_count(
        session.average_pace_seconds_per_kilometer for session in bucket_sessions
    )
    average_duration, average_duration_sample_count = average_with_sample_count(
        session.duration_seconds for session in bucket_sessions
    )
    average_index, average_index_sample_count = average_with_sample_count(
        session.duration_pace_index for session in bucket_sessions
    )
    distances = [
        session.distance_meters
        for session in bucket_sessions
        if session.distance_meters is not None
    ]
    return TrainingAggregate(
        group_id=group_id,
        resolution=resolution,
        bucket_start=bucket.start,
        bucket_end=bucket.end,
        timezone=timezone,
        aggregation_version=aggregation_version,
        session_count=len(bucket_sessions),
        total_distance_meters=sum(distances) if distances else None,
        average_heart_rate=average_heart_rate,
        average_heart_rate_sample_count=average_heart_rate_sample_count,
        average_pace_seconds_per_kilometer=average_pace,
        average_pace_sample_count=average_pace_sample_count,
        average_duration_seconds=average_duration,
        average_duration_sample_count=average_duration_sample_count,
        average_duration_pace_index=average_index,
        average_duration_pace_index_sample_count=average_index_sample_count,
    )


def average_with_sample_count(values: Iterable[int | float | None]) -> tuple[float | None, int]:
    available = [float(value) for value in values if value is not None]
    if not available:
        return None, 0
    return sum(available) / len(available), len(available)
