from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from polar_app.config import Settings
from polar_app.db import create_session_factory, create_sqlite_engine
from polar_app.models.base import Base
from polar_app.models.polar import PolarRawPayload, PolarTrainingSession


def test_training_session_retains_raw_payload_and_rejects_duplicate_external_id(tmp_path):
    engine = create_sqlite_engine(Settings(database_path=tmp_path / "polar.sqlite3"))
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)
    fetched_at = datetime(2026, 9, 2, 8, tzinfo=UTC)

    with session_factory.begin() as session:
        raw_payload = PolarRawPayload(
            endpoint="/v3/exercises/abc123",
            external_id="abc123",
            fetched_at=fetched_at,
            payload_json={"id": "abc123"},
            content_hash="a" * 64,
        )
        session.add(raw_payload)
        session.flush()
        session.add(
            PolarTrainingSession(
                external_id="abc123",
                sport_type="RUNNING",
                sport_name="Running",
                started_at=fetched_at,
                ended_at=fetched_at + timedelta(minutes=30),
                local_date=date(2026, 9, 2),
                duration_seconds=1800,
                distance_meters=5000,
                average_speed_meters_per_second=2.78,
                average_pace_seconds_per_kilometer=360,
                average_heart_rate=140,
                maximum_heart_rate=160,
                calories=350,
                training_load=45,
                raw_payload_id=raw_payload.id,
            )
        )

    with session_factory.begin() as session:
        persisted = session.query(PolarTrainingSession).one()
        assert persisted.raw_payload.content_hash == "a" * 64
        assert persisted.average_pace_seconds_per_kilometer == 360

    with pytest.raises(IntegrityError):
        with session_factory.begin() as session:
            session.add(
                PolarTrainingSession(
                    external_id="abc123",
                    sport_type="RUNNING",
                    started_at=fetched_at,
                    local_date=date(2026, 9, 2),
                    raw_payload_id=1,
                )
            )
            session.flush()

    engine.dispose()
