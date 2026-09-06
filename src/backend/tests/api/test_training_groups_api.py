from datetime import UTC, date, datetime

import httpx
import pytest

from polar_app.config import Settings
from polar_app.main import create_app
from polar_app.models.base import Base
from polar_app.models.polar import PolarRawPayload, PolarTrainingSession
from polar_app.models.training_aggregates import TrainingAggregate


@pytest.mark.anyio
async def test_training_group_can_be_created_and_listed(tmp_path) -> None:
    app = create_app(Settings(database_path=tmp_path / "polar.sqlite3"))
    Base.metadata.create_all(app.state.engine)
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        created = await client.post(
            "/api/training/groups",
            json={"name": "Running", "slug": "running", "color": "#006f7b"},
        )
        listed = await client.get("/api/training/groups")
        series = await client.get("/api/training/groups/1/series", params={"range": "4w"})

    assert created.status_code == 201
    assert created.json() == {
        "id": 1,
        "name": "Running",
        "slug": "running",
        "color": "#006f7b",
        "position": 0,
        "enabled": True,
    }
    assert listed.json() == [created.json()]
    assert series.status_code == 200
    assert series.json()["group"] == created.json()
    assert series.json()["range"] == "4w"
    assert series.json()["resolution"] == "day"
    assert len(series.json()["buckets"]) == 28
    assert all(bucket["session_count"] == 0 for bucket in series.json()["buckets"])


@pytest.mark.anyio
async def test_observed_sport_type_can_be_mapped_to_a_training_group(tmp_path) -> None:
    app = create_app(Settings(database_path=tmp_path / "polar.sqlite3"))
    Base.metadata.create_all(app.state.engine)
    with app.state.session_factory() as session:
        raw = PolarRawPayload(
            endpoint="/v3/exercises",
            external_id="exercise-1",
            fetched_at=datetime.now(UTC),
            payload_json={"id": "exercise-1"},
            content_hash="a" * 64,
        )
        session.add(raw)
        session.flush()
        session.add(
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
            )
        )
        session.commit()
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        group = await client.post(
            "/api/training/groups",
            json={"name": "Running", "slug": "running", "color": "#006f7b"},
        )
        observed = await client.get("/api/training/sport-types")
        mapped = await client.put(
            "/api/training/sport-types/RUNNING",
            json={"state": "mapped", "group_id": group.json()["id"]},
        )
        series = await client.get("/api/training/groups/1/series", params={"range": "all"})
        bucket_sessions = await client.get(
            "/api/training/groups/1/sessions",
            params={"start": "2026-09-01", "end": "2026-10-01"},
        )

    assert observed.json() == [
        {"sport_type": "RUNNING", "session_count": 1, "state": "unmapped", "group_id": None}
    ]
    assert mapped.json() == {
        "sport_type": "RUNNING",
        "session_count": 1,
        "state": "mapped",
        "group_id": 1,
    }
    assert series.json()["resolution"] == "month"
    assert series.json()["aggregation_method"] == "arithmetic_mean_per_session"
    assert series.json()["buckets"] == [
        {
            "date": "2026-09-01",
            "end_date": "2026-10-01",
            "session_count": 1,
            "total_distance_meters": None,
            "average_heart_rate": 140,
            "average_pace_seconds_per_kilometer": 360,
            "average_duration_seconds": 1800,
            "average_duration_pace_index": 5,
            "average_heart_rate_sample_count": 1,
            "average_pace_sample_count": 1,
            "average_duration_sample_count": 1,
            "average_duration_pace_index_sample_count": 1,
        }
    ]
    assert bucket_sessions.json() == [
        {
            "external_id": "exercise-1",
            "local_date": "2026-09-02",
            "sport_type": "RUNNING",
            "duration_seconds": 1800,
            "average_heart_rate": 140,
            "average_pace_seconds_per_kilometer": 360,
            "duration_pace_index": 5,
        }
    ]
    with app.state.session_factory() as session:
        assert session.query(TrainingAggregate).count() == 3


@pytest.mark.anyio
async def test_deleting_a_training_group_unmaps_sport_types_and_removes_aggregates(
    tmp_path,
) -> None:
    app = create_app(Settings(database_path=tmp_path / "polar.sqlite3"))
    Base.metadata.create_all(app.state.engine)
    with app.state.session_factory() as session:
        raw = PolarRawPayload(
            endpoint="/v3/exercises",
            external_id="exercise-1",
            fetched_at=datetime.now(UTC),
            payload_json={"id": "exercise-1"},
            content_hash="a" * 64,
        )
        session.add(raw)
        session.flush()
        session.add(
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
            )
        )
        session.commit()
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        group = await client.post(
            "/api/training/groups",
            json={"name": "Running", "slug": "running", "color": "#006f7b"},
        )
        group_id = group.json()["id"]
        await client.put(
            "/api/training/sport-types/RUNNING",
            json={"state": "mapped", "group_id": group_id},
        )
        deleted = await client.request(
            "DELETE", f"/api/training/groups/{group_id}", json={"disposition": "unmapped"}
        )
        groups = await client.get("/api/training/groups")
        sport_types = await client.get("/api/training/sport-types")

    assert deleted.status_code == 204
    assert groups.json() == []
    assert sport_types.json() == [
        {"sport_type": "RUNNING", "session_count": 1, "state": "unmapped", "group_id": None}
    ]
    with app.state.session_factory() as session:
        assert session.query(TrainingAggregate).count() == 0


@pytest.mark.anyio
async def test_deleting_a_training_group_can_reassign_its_sport_types(tmp_path) -> None:
    app = create_app(Settings(database_path=tmp_path / "polar.sqlite3"))
    Base.metadata.create_all(app.state.engine)
    with app.state.session_factory() as session:
        raw = PolarRawPayload(
            endpoint="/v3/exercises",
            external_id="exercise-1",
            fetched_at=datetime.now(UTC),
            payload_json={"id": "exercise-1"},
            content_hash="a" * 64,
        )
        session.add(raw)
        session.flush()
        session.add(
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
            )
        )
        session.commit()
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        running = await client.post(
            "/api/training/groups",
            json={"name": "Running", "slug": "running", "color": "#006f7b"},
        )
        walking = await client.post(
            "/api/training/groups",
            json={"name": "Walking", "slug": "walking", "color": "#216869"},
        )
        await client.put(
            "/api/training/sport-types/RUNNING",
            json={"state": "mapped", "group_id": running.json()["id"]},
        )
        deleted = await client.request(
            "DELETE",
            f"/api/training/groups/{running.json()['id']}",
            json={"disposition": "reassign", "replacement_group_id": walking.json()["id"]},
        )
        sport_types = await client.get("/api/training/sport-types")
        series = await client.get(
            f"/api/training/groups/{walking.json()['id']}/series", params={"range": "all"}
        )

    assert deleted.status_code == 204
    assert sport_types.json() == [
        {
            "sport_type": "RUNNING",
            "session_count": 1,
            "state": "mapped",
            "group_id": walking.json()["id"],
        }
    ]
    assert series.json()["buckets"][0]["session_count"] == 1
