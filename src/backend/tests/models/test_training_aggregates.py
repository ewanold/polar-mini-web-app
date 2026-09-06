from datetime import date

from sqlalchemy.exc import IntegrityError

from polar_app.config import Settings
from polar_app.db import create_session_factory, create_sqlite_engine
from polar_app.models.base import Base
from polar_app.models.training_aggregates import TrainingAggregate
from polar_app.models.training_groups import TrainingGroup


def test_aggregate_is_unique_per_group_resolution_bucket_and_timezone(tmp_path) -> None:
    engine = create_sqlite_engine(Settings(database_path=tmp_path / "polar.sqlite3"))
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        group = TrainingGroup(name="Running", slug="running", color="#006f7b")
        session.add(group)
        session.flush()
        session.add_all(
            [
                TrainingAggregate(
                    group_id=group.id,
                    resolution="day",
                    bucket_start=date(2026, 9, 3),
                    bucket_end=date(2026, 9, 4),
                    timezone="Europe/Berlin",
                    session_count=1,
                ),
                TrainingAggregate(
                    group_id=group.id,
                    resolution="day",
                    bucket_start=date(2026, 9, 3),
                    bucket_end=date(2026, 9, 4),
                    timezone="UTC",
                    session_count=1,
                ),
            ]
        )
        session.commit()

        session.add(
            TrainingAggregate(
                group_id=group.id,
                resolution="day",
                bucket_start=date(2026, 9, 3),
                bucket_end=date(2026, 9, 4),
                timezone="Europe/Berlin",
                session_count=1,
            )
        )
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
        else:
            raise AssertionError("duplicate aggregate bucket was accepted")

    engine.dispose()


def test_aggregate_keeps_missing_metric_values_null_with_zero_sample_counts(tmp_path) -> None:
    engine = create_sqlite_engine(Settings(database_path=tmp_path / "polar.sqlite3"))
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        group = TrainingGroup(name="Walking", slug="walking", color="#216869")
        session.add(group)
        session.flush()
        session.add(
            TrainingAggregate(
                group_id=group.id,
                resolution="week",
                bucket_start=date(2026, 8, 31),
                bucket_end=date(2026, 9, 7),
                timezone="Europe/Berlin",
                session_count=2,
            )
        )
        session.commit()
        aggregate = session.query(TrainingAggregate).one()

    assert aggregate.average_heart_rate is None
    assert aggregate.average_pace_seconds_per_kilometer is None
    assert aggregate.average_duration_seconds is None
    assert aggregate.average_duration_pace_index is None
    assert aggregate.average_heart_rate_sample_count == 0
    assert aggregate.average_pace_sample_count == 0
    assert aggregate.average_duration_sample_count == 0
    assert aggregate.average_duration_pace_index_sample_count == 0
    engine.dispose()
