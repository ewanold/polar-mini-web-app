from datetime import UTC, date, datetime

import httpx
import pytest

from polar_app.config import Settings
from polar_app.main import create_app
from polar_app.models.base import Base
from polar_app.models.polar import (
    PolarActivityDay,
    PolarHeartRateSample,
    PolarRawPayload,
    PolarSleepDay,
)


@pytest.mark.anyio
async def test_timeline_returns_ordered_daily_sleep_activity_and_heart_rate_data(tmp_path) -> None:
    app = create_app(Settings(database_path=tmp_path / "polar.sqlite3"))
    Base.metadata.create_all(app.state.engine)
    with app.state.session_factory() as session:
        raw = PolarRawPayload(
            endpoint="/test/timeline",
            external_id="timeline-source",
            fetched_at=datetime.now(UTC),
            payload_json={"source": "test"},
            content_hash="a" * 64,
        )
        session.add(raw)
        session.flush()
        session.add_all(
            [
                PolarSleepDay(
                    sleep_date=date(2026, 9, 1),
                    start_time=datetime(2026, 8, 31, 22, 30, tzinfo=UTC),
                    end_time=datetime(2026, 9, 1, 6, 30, tzinfo=UTC),
                    duration_seconds=28_800,
                    score=82,
                    raw_payload_id=raw.id,
                ),
                PolarActivityDay(
                    activity_date=date(2026, 9, 1),
                    active_steps=9_840,
                    active_calories=612,
                    raw_payload_id=raw.id,
                ),
                PolarHeartRateSample(
                    sampled_at=datetime(2026, 9, 1, 8, 0),
                    heart_rate=58,
                    raw_payload_id=raw.id,
                ),
                PolarHeartRateSample(
                    sampled_at=datetime(2026, 9, 1, 12, 0),
                    heart_rate=92,
                    raw_payload_id=raw.id,
                ),

            ]
        )
        session.commit()
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/timeline", params={"start": "2026-09-01", "end": "2026-09-02"}
        )

    assert response.status_code == 200
    assert response.json() == {
        "start": "2026-09-01",
        "end": "2026-09-02",
        "days": [
            {
                "date": "2026-09-01",
                "sleep": {
                    "duration_seconds": 28_800,
                    "score": 82,
                    "start_time": "2026-08-31T22:30:00",
                    "end_time": "2026-09-01T06:30:00",
                },
                "activity": {"active_steps": 9_840, "active_calories": 612},
                "nightly_recharge": None,

                "heart_rate": {
                    "average": 75,
                    "minimum": 58,
                    "maximum": 92,
                    "samples": [
                        {"sampled_at": "2026-09-01T08:00:00", "heart_rate": 58},
                        {"sampled_at": "2026-09-01T12:00:00", "heart_rate": 92},
                    ],
                },
                "events": [],
            },
            {
                "date": "2026-09-02",
                "sleep": None,
                "activity": None,
                "nightly_recharge": None,

                "heart_rate": None,
                "events": [],
            },
        ],
    }


@pytest.mark.anyio
async def test_timeline_event_is_saved_and_returned_on_its_date(tmp_path) -> None:
    app = create_app(Settings(database_path=tmp_path / "polar.sqlite3"))
    Base.metadata.create_all(app.state.engine)
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        created = await client.post(
            "/api/timeline/events",
            json={"date": "2026-09-01", "description": "Late dinner"},
        )
        timeline = await client.get(
            "/api/timeline", params={"start": "2026-09-01", "end": "2026-09-02"}
        )

    assert created.status_code == 201
    assert created.json() == {"id": 1, "date": "2026-09-01", "description": "Late dinner"}
    assert timeline.json()["days"][0]["events"] == [
        {"id": 1, "date": "2026-09-01", "description": "Late dinner"}
    ]
    assert timeline.json()["days"][1]["events"] == []


@pytest.mark.anyio
async def test_timeline_event_description_can_be_updated(tmp_path) -> None:
    app = create_app(Settings(database_path=tmp_path / "polar.sqlite3"))
    Base.metadata.create_all(app.state.engine)
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        created = await client.post(
            "/api/timeline/events",
            json={"date": "2026-09-01", "description": "Late dinner"},
        )
        updated = await client.put(
            f"/api/timeline/events/{created.json()['id']}",
            json={"description": "Late dinner and dessert"},
        )
        timeline = await client.get(
            "/api/timeline", params={"start": "2026-09-01", "end": "2026-09-01"}
        )

    assert updated.status_code == 200
    assert updated.json() == {
        "id": 1,
        "date": "2026-09-01",
        "description": "Late dinner and dessert",
    }
    assert timeline.json()["days"][0]["events"] == [updated.json()]


@pytest.mark.anyio
async def test_timeline_event_can_be_deleted(tmp_path) -> None:
    app = create_app(Settings(database_path=tmp_path / "polar.sqlite3"))
    Base.metadata.create_all(app.state.engine)
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        created = await client.post(
            "/api/timeline/events",
            json={"date": "2026-09-01", "description": "Late dinner"},
        )
        deleted = await client.delete(f"/api/timeline/events/{created.json()['id']}")
        timeline = await client.get(
            "/api/timeline", params={"start": "2026-09-01", "end": "2026-09-01"}
        )

    assert deleted.status_code == 204
    assert timeline.json()["days"][0]["events"] == []
