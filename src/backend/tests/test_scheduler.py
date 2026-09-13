import pytest

from polar_app.config import Settings
from polar_app.db import create_session_factory, create_sqlite_engine
from polar_app.models.base import Base
from polar_app.models.sync import PolarSyncState
from polar_app.scheduler import PolarScheduler


@pytest.mark.anyio
async def test_scheduler_does_not_mark_a_partial_category_failure_as_success(
    tmp_path, monkeypatch
) -> None:
    settings = Settings(database_path=tmp_path / "polar.sqlite3")
    engine = create_sqlite_engine(settings)
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)

    async def partial_failure(*_args, **_kwargs):
        return {
            "connected": True,
            "categories": {"continuous_heart_rate": {"error": "unavailable"}},
        }

    monkeypatch.setattr("polar_app.scheduler.synchronize", partial_failure)
    scheduler = PolarScheduler(session_factory, settings)

    await scheduler.run_once()

    with session_factory() as session:
        state = session.get(PolarSyncState, "all")
        assert state is not None
        assert state.last_success_at is None
        assert state.last_error == "continuous_heart_rate"
