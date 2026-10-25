from datetime import UTC, date, datetime, timedelta

import httpx
import pytest

from polar_app.config import Settings
from polar_app.main import create_app
from polar_app.models.base import Base
from polar_app.models.polar import PolarCardioLoad, PolarRawPayload


@pytest.mark.anyio
async def test_training_cardio_load_ranges_work_without_a_training_group(tmp_path):
    app = create_app(Settings(database_path=tmp_path / "polar.sqlite3"))
    Base.metadata.create_all(app.state.engine)
    today = date.today()
    older = today - timedelta(days=50)
    with app.state.session_factory.begin() as session:
        raw = PolarRawPayload(
            endpoint="/test",
            external_id="cardio",
            fetched_at=datetime.now(UTC),
            payload_json={},
            content_hash="a" * 64,
        )
        session.add(raw)
        session.flush()
        session.add_all(
            [
                PolarCardioLoad(load_date=older, strain=25, tolerance=30, raw_payload_id=raw.id),
                PolarCardioLoad(load_date=today, strain=0, tolerance=None, raw_payload_id=raw.id),
            ]
        )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        short = await client.get("/api/training/cardio-load?range=4w")
        long = await client.get("/api/training/cardio-load?range=6m")
        all_data = await client.get("/api/training/cardio-load?range=all")
    assert short.status_code == long.status_code == all_data.status_code == 200
    assert short.json()["days"] == [
        {"date": today.isoformat(), "cardio_load": {"strain": 0, "tolerance": None}}
    ]
    assert len(long.json()["days"]) == len(all_data.json()["days"]) == 2
    assert all_data.json()["start"] == older.replace(day=1).isoformat()
