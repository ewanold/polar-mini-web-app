from datetime import UTC, datetime

import httpx
import pytest

from polar_app.config import Settings
from polar_app.main import create_app
from polar_app.models.base import Base
from polar_app.models.sync import PolarSyncState


@pytest.mark.anyio
async def test_polar_status_includes_last_successful_sync(tmp_path) -> None:
    app = create_app(Settings(database_path=tmp_path / "polar.sqlite3"))
    Base.metadata.create_all(app.state.engine)
    completed_at = datetime(2026, 9, 6, 10, 15, tzinfo=UTC)
    with app.state.session_factory.begin() as session:
        session.add(PolarSyncState(category="all", last_success_at=completed_at))

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/polar/status")

    assert response.status_code == 200
    assert response.json()["last_success_at"] == "2026-09-06T10:15:00+00:00"
