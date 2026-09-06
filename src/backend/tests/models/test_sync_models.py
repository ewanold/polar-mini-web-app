from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError

from polar_app.config import Settings
from polar_app.db import create_session_factory, create_sqlite_engine
from polar_app.models.base import Base
from polar_app.models.sync import PolarSyncState


def test_sync_state_is_unique_per_category_and_records_failures(tmp_path):
    engine = create_sqlite_engine(Settings(database_path=tmp_path / "polar.sqlite3"))
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)
    attempted_at = datetime(2026, 9, 2, 9, tzinfo=UTC)

    with session_factory.begin() as session:
        session.add(
            PolarSyncState(
                category="training",
                cursor="2026-09-01",
                window_start="2026-08-01",
                last_attempt_at=attempted_at,
                last_success_at=None,
                last_error="rate limited",
            )
        )

    with pytest.raises(IntegrityError):
        with session_factory.begin() as session:
            session.add(
                PolarSyncState(
                    category="training",
                    cursor=None,
                    window_start=None,
                    last_attempt_at=attempted_at,
                    last_success_at=attempted_at,
                    last_error=None,
                )
            )
            session.flush()

    engine.dispose()
