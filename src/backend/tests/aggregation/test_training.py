from datetime import UTC, date, datetime

from polar_app.aggregation.buckets import Bucket
from polar_app.aggregation.training import calculate_training_aggregate
from polar_app.models.polar import PolarTrainingSession


def session(
    external_id: str,
    local_date: date,
    *,
    heart_rate: int | None = None,
    pace: float | None = None,
    duration: int | None = None,
    index: float | None = None,
    distance: float | None = None,
) -> PolarTrainingSession:
    return PolarTrainingSession(
        external_id=external_id,
        sport_type="RUNNING",
        started_at=datetime(2026, 9, 1, tzinfo=UTC),
        local_date=local_date,
        average_heart_rate=heart_rate,
        average_pace_seconds_per_kilometer=pace,
        duration_seconds=duration,
        duration_pace_index=index,
        distance_meters=distance,
        raw_payload_id=1,
    )


def test_calculation_averages_each_metric_from_available_sessions() -> None:
    aggregate = calculate_training_aggregate(
        group_id=7,
        resolution="day",
        bucket=Bucket(start=date(2026, 9, 2), end=date(2026, 9, 3)),
        timezone="Europe/Berlin",
        sessions=[
            session(
                "one", date(2026, 9, 2), heart_rate=120, pace=300,
                duration=1800, index=6, distance=5000,
            ),
            session("two", date(2026, 9, 2), pace=360, distance=2000),
            session(
                "three", date(2026, 9, 2), heart_rate=150, duration=2400,
                index=5.5, distance=3000,
            ),
            session("outside", date(2026, 9, 3), heart_rate=210, pace=120, duration=600, index=5),
        ],
    )

    assert aggregate is not None
    assert aggregate.session_count == 3
    assert aggregate.average_heart_rate == 135
    assert aggregate.average_heart_rate_sample_count == 2
    assert aggregate.average_pace_seconds_per_kilometer == 330
    assert aggregate.average_pace_sample_count == 2
    assert aggregate.average_duration_seconds == 2100
    assert aggregate.average_duration_sample_count == 2
    assert aggregate.average_duration_pace_index == 5.75
    assert aggregate.average_duration_pace_index_sample_count == 2
    assert aggregate.total_distance_meters == 10_000


def test_calculation_omits_empty_buckets_instead_of_persisting_zero_values() -> None:
    aggregate = calculate_training_aggregate(
        group_id=7,
        resolution="month",
        bucket=Bucket(start=date(2026, 9, 1), end=date(2026, 10, 1)),
        timezone="Europe/Berlin",
        sessions=[session("outside", date(2026, 10, 1), heart_rate=120)],
    )

    assert aggregate is None


def test_calculation_preserves_null_metric_values_and_zero_sample_counts() -> None:
    aggregate = calculate_training_aggregate(
        group_id=7,
        resolution="week",
        bucket=Bucket(start=date(2026, 8, 31), end=date(2026, 9, 7)),
        timezone="Europe/Berlin",
        sessions=[session("one", date(2026, 9, 2))],
    )

    assert aggregate is not None
    assert aggregate.session_count == 1
    assert aggregate.average_heart_rate is None
    assert aggregate.average_heart_rate_sample_count == 0
    assert aggregate.average_pace_seconds_per_kilometer is None
    assert aggregate.average_pace_sample_count == 0
    assert aggregate.average_duration_seconds is None
    assert aggregate.average_duration_sample_count == 0
    assert aggregate.average_duration_pace_index is None
    assert aggregate.average_duration_pace_index_sample_count == 0
