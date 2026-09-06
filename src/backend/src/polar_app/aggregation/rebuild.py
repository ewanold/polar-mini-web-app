from collections.abc import Iterable
from datetime import date

from sqlalchemy.orm import Session

from polar_app.aggregation.buckets import Bucket, day_bucket, month_bucket, week_bucket
from polar_app.aggregation.training import calculate_training_aggregate
from polar_app.models.polar import PolarTrainingSession
from polar_app.models.training_aggregates import AggregationResolution, TrainingAggregate
from polar_app.models.training_groups import PolarSportTypeMapping

AGGREGATION_VERSION = 1


def rebuild_group_buckets(
    session: Session, *, group_ids: Iterable[int], local_dates: Iterable[date], timezone: str
) -> int:
    """Replace every affected aggregate bucket for the supplied groups and session dates."""
    group_ids = tuple(group_ids)
    local_dates = tuple(local_dates)
    affected = {
        (group_id, resolution, bucket.start, bucket.end)
        for group_id in group_ids
        for local_date in local_dates
        for resolution, bucket in (
            ("day", day_bucket(local_date)),
            ("week", week_bucket(local_date)),
            ("month", month_bucket(local_date)),
        )
    }
    for group_id, resolution, bucket_start, bucket_end in affected:
        rebuild_bucket(
            session,
            group_id=group_id,
            resolution=resolution,
            bucket_start=bucket_start,
            bucket_end=bucket_end,
            timezone=timezone,
        )
    return len(affected)


def rebuild_bucket(
    session: Session,
    *,
    group_id: int,
    resolution: AggregationResolution,
    bucket_start: date,
    bucket_end: date,
    timezone: str,
) -> None:
    session.query(TrainingAggregate).filter_by(
        group_id=group_id,
        resolution=resolution,
        bucket_start=bucket_start,
        timezone=timezone,
    ).delete(synchronize_session=False)
    mapped_sessions = (
        session.query(PolarTrainingSession)
        .join(
            PolarSportTypeMapping,
            PolarSportTypeMapping.sport_type == PolarTrainingSession.sport_type,
        )
        .filter(
            PolarSportTypeMapping.group_id == group_id,
            PolarSportTypeMapping.state == "mapped",
            PolarTrainingSession.local_date >= bucket_start,
            PolarTrainingSession.local_date < bucket_end,
        )
        .all()
    )
    aggregate = calculate_training_aggregate(
        group_id=group_id,
        resolution=resolution,
        bucket=Bucket(start=bucket_start, end=bucket_end),
        timezone=timezone,
        sessions=mapped_sessions,
        aggregation_version=AGGREGATION_VERSION,
    )
    if aggregate is not None:
        session.add(aggregate)


def rebuild_all_training_aggregates(session: Session, *, timezone: str) -> int:
    """Discard caches and rebuild all resolutions directly from mapped normalized sessions."""
    affected_rows = (
        session.query(PolarSportTypeMapping.group_id, PolarTrainingSession.local_date)
        .join(
            PolarTrainingSession,
            PolarTrainingSession.sport_type == PolarSportTypeMapping.sport_type,
        )
        .filter(
            PolarSportTypeMapping.state == "mapped",
            PolarSportTypeMapping.group_id.is_not(None),
        )
        .distinct()
        .all()
    )
    affected = {
        (group_id, resolution, bucket.start, bucket.end)
        for group_id, local_date in affected_rows
        for resolution, bucket in (
            ("day", day_bucket(local_date)),
            ("week", week_bucket(local_date)),
            ("month", month_bucket(local_date)),
        )
    }
    session.query(TrainingAggregate).delete(synchronize_session=False)
    for group_id, resolution, bucket_start, bucket_end in affected:
        rebuild_bucket(
            session,
            group_id=group_id,
            resolution=resolution,
            bucket_start=bucket_start,
            bucket_end=bucket_end,
            timezone=timezone,
        )
    return len(affected)
