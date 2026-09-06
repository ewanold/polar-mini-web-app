import asyncio
from datetime import date

from polar_app.config import Settings
from polar_app.db import create_session_factory, create_sqlite_engine
from polar_app.models.base import Base
from polar_app.models.polar import PolarTrainingSession
from polar_app.models.training_aggregates import TrainingAggregate
from polar_app.models.training_groups import PolarSportTypeMapping, TrainingGroup
from polar_app.polar.sync_training import (
    import_training_payload,
    parse_duration_seconds,
    sync_training,
)


def test_duration_parser_accepts_clock_duration() -> None:
    assert parse_duration_seconds("01:02:03") == 3723
    assert parse_duration_seconds("00:30:00.000") == 1800
    assert parse_duration_seconds("PT3826.778S") == 3827


def test_training_import_normalizes_duration_speed_pace_and_is_idempotent(tmp_path) -> None:
    engine = create_sqlite_engine(Settings(database_path=tmp_path / "polar.sqlite3"))
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)
    payload = {
        "id": "exercise-1",
        "start_time": "2026-09-02T10:00:00",
        "start_time_utc_offset": 120,
        "duration": "PT30M",
        "distance": 5000,
        "calories": 320,
        "heart_rate": {"average": 140, "maximum": 165},
        "training_load": 42.5,
        "sport": "RUNNING",
        "detailed_sport_info": "RUNNING_TRAIL",
    }

    with session_factory() as session:
        first_result = import_training_payload(session, payload, timezone="Europe/Berlin")
        session.commit()
    with session_factory() as session:
        second_result = import_training_payload(session, payload, timezone="Europe/Berlin")
        session.commit()
        training = session.query(PolarTrainingSession).one()

    assert first_result == "inserted"
    assert second_result == "skipped"
    assert training.local_date == date(2026, 9, 2)
    assert training.duration_seconds == 1800
    assert training.average_speed_meters_per_second == 2.7777777777777777
    assert training.average_pace_seconds_per_kilometer == 360
    assert training.duration_pace_index == 5
    assert training.sport_type == "RUNNING_TRAIL"
    engine.dispose()


def test_training_sync_returns_inserted_updated_and_skipped_counts(tmp_path) -> None:
    class Client:
        async def get(self, path: str) -> object:
            assert path == "/v3/exercises"
            return [
                {
                    "id": "exercise-1",
                    "start_time": "2026-09-02T10:00:00",
                    "start_time_utc_offset": 120,
                    "duration": "PT30M",
                    "distance": 5000,
                    "sport": "RUNNING",
                }
            ]

    engine = create_sqlite_engine(Settings(database_path=tmp_path / "polar.sqlite3"))
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        group = TrainingGroup(name="Running", slug="running", color="#006f7b")
        session.add(group)
        session.flush()
        session.add(PolarSportTypeMapping(sport_type="RUNNING", state="mapped", group_id=group.id))
        session.commit()
    with session_factory() as session:
        result = asyncio.run(sync_training(session, Client(), timezone="Europe/Berlin"))
        session.commit()
        assert session.query(TrainingAggregate).count() == 3

    assert result == {"inserted": 1, "updated": 0, "skipped": 0, "errors": 0}
    engine.dispose()


def test_training_sync_fetches_detail_for_exercise_references(tmp_path) -> None:
    class Client:
        async def get(self, path: str) -> object:
            if path == "/v3/exercises":
                return [{"id": "exercise-1"}]
            assert path == "/v3/exercises/exercise-1"
            return {
                "id": "exercise-1", "start_time": "2026-09-02T10:00:00",
                "duration": "PT30M", "sport": "RUNNING",
            }

    engine = create_sqlite_engine(Settings(database_path=tmp_path / "polar.sqlite3"))
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        result = asyncio.run(sync_training(session, Client(), timezone="Europe/Berlin"))
        session.commit()

    assert result == {"inserted": 1, "updated": 0, "skipped": 0, "errors": 0}
    engine.dispose()
