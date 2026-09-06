from datetime import UTC, date, datetime

from sqlalchemy.orm import Session

from polar_app.aggregation.rebuild import rebuild_all_training_aggregates, rebuild_group_buckets
from polar_app.config import Settings
from polar_app.db import create_session_factory, create_sqlite_engine
from polar_app.models.base import Base
from polar_app.models.polar import PolarRawPayload, PolarTrainingSession
from polar_app.models.training_aggregates import TrainingAggregate
from polar_app.models.training_groups import PolarSportTypeMapping, TrainingGroup


def test_incremental_rebuild_matches_a_clean_full_rebuild(tmp_path) -> None:
    engine = create_sqlite_engine(Settings(database_path=tmp_path / "polar.sqlite3"))
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        running = TrainingGroup(name="Running", slug="running", color="#006f7b")
        raw = PolarRawPayload(
            endpoint="/v3/exercises",
            external_id="exercise-1",
            fetched_at=datetime.now(UTC),
            payload_json={"id": "exercise-1"},
            content_hash="a" * 64,
        )
        session.add_all([running, raw])
        session.flush()
        session.add(
            PolarSportTypeMapping(sport_type="RUNNING", state="mapped", group_id=running.id)
        )
        session.add_all(
            [
                PolarTrainingSession(
                    external_id="exercise-1",
                    sport_type="RUNNING",
                    started_at=datetime(2026, 9, 2, tzinfo=UTC),
                    local_date=date(2026, 9, 2),
                    duration_seconds=1800,
                    average_heart_rate=140,
                    average_pace_seconds_per_kilometer=360,
                    duration_pace_index=5,
                    raw_payload_id=raw.id,
                ),
                PolarTrainingSession(
                    external_id="exercise-2",
                    sport_type="RUNNING",
                    started_at=datetime(2026, 9, 3, tzinfo=UTC),
                    local_date=date(2026, 9, 3),
                    duration_seconds=2400,
                    average_heart_rate=150,
                    average_pace_seconds_per_kilometer=400,
                    duration_pace_index=6,
                    raw_payload_id=raw.id,
                ),
            ]
        )
        session.commit()

    with session_factory() as session:
        rebuild_group_buckets(
            session,
            group_ids=[1],
            local_dates=[date(2026, 9, 2), date(2026, 9, 3)],
            timezone="Europe/Berlin",
        )
        session.commit()
        incremental = aggregate_snapshot(session)

        rebuilt = rebuild_all_training_aggregates(session, timezone="Europe/Berlin")
        session.commit()
        full = aggregate_snapshot(session)

    assert rebuilt == 4
    assert incremental == full
    engine.dispose()


def test_rebuild_deletes_an_aggregate_that_becomes_empty(tmp_path) -> None:
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
                resolution="day",
                bucket_start=date(2026, 9, 2),
                bucket_end=date(2026, 9, 3),
                timezone="Europe/Berlin",
                session_count=1,
            )
        )
        rebuild_group_buckets(
            session,
            group_ids=[group.id],
            local_dates=[date(2026, 9, 2)],
            timezone="Europe/Berlin",
        )
        session.commit()
        assert session.query(TrainingAggregate).count() == 0

    engine.dispose()


def aggregate_snapshot(session: Session) -> list[tuple[object, ...]]:
    return [
        (
            aggregate.group_id,
            aggregate.resolution,
            aggregate.bucket_start,
            aggregate.bucket_end,
            aggregate.session_count,
            aggregate.average_heart_rate,
            aggregate.average_pace_seconds_per_kilometer,
            aggregate.average_duration_seconds,
            aggregate.average_duration_pace_index,
        )
        for aggregate in session.query(TrainingAggregate)
        .order_by(TrainingAggregate.resolution, TrainingAggregate.bucket_start)
        .all()
    ]
