import asyncio
from datetime import date

from polar_app.config import Settings
from polar_app.db import create_session_factory, create_sqlite_engine
from polar_app.models.base import Base
from polar_app.models.polar import PolarCardioLoad, PolarRawPayload
from polar_app.polar.sync_daily import sync_cardio_load


def test_cardio_load_sync_retains_raw_values_updates_and_preserves_missing_data(tmp_path):
    rows = [
        {"date": "2026-09-01", "strain": 0, "tolerance": 42.5},
        {"date": "2026-09-02", "cardio_load_status": "LOAD_STATUS_NOT_AVAILABLE"},
    ]

    class Client:
        async def get(self, path):
            assert path == "/v3/users/cardio-load"
            return rows

    engine = create_sqlite_engine(Settings(database_path=tmp_path / "polar.sqlite3"))
    Base.metadata.create_all(engine)
    factory = create_session_factory(engine)
    with factory.begin() as session:
        assert asyncio.run(sync_cardio_load(session, Client())) == {
            "inserted": 2, "updated": 0, "skipped": 0, "errors": 0,
        }
    with factory.begin() as session:
        assert asyncio.run(sync_cardio_load(session, Client()))["skipped"] == 2
    rows[0]["strain"] = 21.5
    with factory.begin() as session:
        assert asyncio.run(sync_cardio_load(session, Client()))["updated"] == 1
        load = session.query(PolarCardioLoad).filter_by(load_date=date(2026, 9, 1)).one()
        assert (load.strain, load.tolerance) == (21.5, 42.5)
        missing = session.query(PolarCardioLoad).filter_by(load_date=date(2026, 9, 2)).one()
        assert (missing.strain, missing.tolerance) == (None, None)
        assert session.query(PolarRawPayload).count() == 2
    engine.dispose()
