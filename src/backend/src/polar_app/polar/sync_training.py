import hashlib
import json
import re
from datetime import UTC, datetime, timedelta
from datetime import timezone as fixed_timezone
from typing import Any, Protocol
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from polar_app.aggregation.rebuild import rebuild_group_buckets
from polar_app.models.polar import PolarRawPayload, PolarTrainingSession
from polar_app.models.training_groups import PolarSportTypeMapping

_DURATION_PATTERN = re.compile(
    r"^PT(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+(?:\.\d+)?)S)?$"
)
_CLOCK_DURATION_PATTERN = re.compile(
    r"^(?P<hours>\d{1,2}):(?P<minutes>[0-5]\d):(?P<seconds>[0-5]\d)(?:\.\d+)?$"
)


class TrainingClient(Protocol):
    async def get(self, path: str) -> object: ...


async def sync_training(
    session: Session, client: TrainingClient, *, timezone: str
) -> dict[str, object]:
    payloads = await client.get("/v3/exercises")
    if not isinstance(payloads, list):
        raise ValueError("Polar exercises response must be a list")
    result = {"inserted": 0, "updated": 0, "skipped": 0, "errors": 0}
    error_samples: list[str] = []
    affected_sport_types: set[str] = set()
    affected_local_dates = set()
    for payload in payloads:
        if isinstance(payload, str):
            path = urlsplit(payload).path
            if not path.startswith("/v3/exercises/"):
                result["errors"] += 1
                if len(error_samples) < 3:
                    error_samples.append("unknown exercise reference format")
                continue
            detail = await client.get(path)
            if not isinstance(detail, dict):
                result["errors"] += 1
                if len(error_samples) < 3:
                    error_samples.append("exercise detail response must be an object")
                continue
            payload = detail
        if not isinstance(payload, dict):
            result["errors"] += 1
            if len(error_samples) < 3:
                error_samples.append("unknown exercise reference format")
            continue
        try:
            if "start_time" not in payload:
                exercise_id = payload.get("id")
                if not isinstance(exercise_id, str):
                    raise ValueError("Polar exercise reference is missing its identifier")
                detail = await client.get(f"/v3/exercises/{exercise_id}")
                if not isinstance(detail, dict):
                    raise ValueError("Polar exercise detail response must be an object")
                payload = detail
            external_id = payload.get("id")
            existing = (
                session.query(PolarTrainingSession).filter_by(external_id=external_id).one_or_none()
                if isinstance(external_id, str)
                else None
            )
            if existing is not None:
                affected_sport_types.add(existing.sport_type)
                affected_local_dates.add(existing.local_date)
            outcome = import_training_payload(session, payload, timezone=timezone)
            result[outcome] += 1
            if outcome != "skipped" and isinstance(external_id, str):
                imported = (
                    session.query(PolarTrainingSession).filter_by(external_id=external_id).one()
                )
                affected_sport_types.add(imported.sport_type)
                affected_local_dates.add(imported.local_date)
        except ValueError as error:
            result["errors"] += 1
            exercise_id = payload.get("id")
            label = exercise_id if isinstance(exercise_id, str) else "unknown exercise"
            if len(error_samples) < 3:
                error_samples.append(f"{label}: {error}")
    if affected_sport_types:
        group_ids = [
            group_id
            for (group_id,) in session.query(PolarSportTypeMapping.group_id)
            .filter(
                PolarSportTypeMapping.sport_type.in_(affected_sport_types),
                PolarSportTypeMapping.state == "mapped",
                PolarSportTypeMapping.group_id.is_not(None),
            )
            .all()
        ]
        if group_ids:
            rebuild_group_buckets(
                session,
                group_ids=group_ids,
                local_dates=affected_local_dates,
                timezone=timezone,
            )
    return result | ({"error_samples": error_samples} if error_samples else {})


def parse_duration_seconds(value: str) -> int:
    match = _DURATION_PATTERN.fullmatch(value)
    if match:
        hours = int(match.group("hours") or 0)
        minutes = int(match.group("minutes") or 0)
        seconds = round(float(match.group("seconds") or 0))
        return hours * 3600 + minutes * 60 + seconds
    match = _CLOCK_DURATION_PATTERN.fullmatch(value)
    if not match:
        raise ValueError(f"Unsupported Polar duration format: {value!r}")
    parts = {key: int(part or 0) for key, part in match.groupdict().items()}
    return parts["hours"] * 3600 + parts["minutes"] * 60 + parts["seconds"]


def import_training_payload(session: Session, payload: dict[str, Any], *, timezone: str) -> str:
    external_id = payload.get("id")
    start_time = payload.get("start_time")
    duration = payload.get("duration")
    sport = payload.get("detailed_sport_info") or payload.get("sport")
    if not all(isinstance(value, str) for value in (external_id, start_time, duration, sport)):
        raise ValueError("Polar exercise payload is missing a required field")

    duration_seconds = parse_duration_seconds(duration)
    start_offset_minutes = payload.get("start_time_utc_offset", 0)
    if not isinstance(start_offset_minutes, int):
        raise ValueError("Polar exercise start_time_utc_offset must be an integer")
    started_at = datetime.fromisoformat(start_time).replace(
        tzinfo=fixed_timezone(timedelta(minutes=start_offset_minutes))
    )
    ended_at = started_at + timedelta(seconds=duration_seconds)
    distance = number_or_none(payload.get("distance"))
    speed = duration_seconds and distance / duration_seconds if distance else None
    pace = 1000 / speed if speed and speed > 0 else None
    duration_pace_index = duration_seconds / 60 / (pace / 60) if pace and pace > 0 else None
    heart_rate = payload.get("heart_rate")
    if not isinstance(heart_rate, dict):
        heart_rate = {}
    raw_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    content_hash = hashlib.sha256(raw_json.encode()).hexdigest()

    existing = session.query(PolarTrainingSession).filter_by(external_id=external_id).one_or_none()
    if existing and existing.raw_payload.content_hash == content_hash:
        return "skipped"
    raw_payload = (
        session.query(PolarRawPayload)
        .filter_by(endpoint="/v3/exercises", external_id=external_id)
        .one_or_none()
    )
    if raw_payload is None:
        raw_payload = PolarRawPayload(
            endpoint="/v3/exercises",
            external_id=external_id,
            fetched_at=datetime.now(UTC),
            payload_json=payload,
            content_hash=content_hash,
        )
        session.add(raw_payload)
        session.flush()
    else:
        raw_payload.fetched_at = datetime.now(UTC)
        raw_payload.payload_json = payload
        raw_payload.content_hash = content_hash

    values = {
        "sport_type": sport,
        "sport_name": payload.get("sport") if isinstance(payload.get("sport"), str) else None,
        "started_at": started_at,
        "ended_at": ended_at,
        "local_date": started_at.astimezone(ZoneInfo(timezone)).date(),
        "duration_seconds": duration_seconds,
        "distance_meters": distance,
        "average_speed_meters_per_second": speed,
        "average_pace_seconds_per_kilometer": pace,
        "duration_pace_index": duration_pace_index,
        "average_heart_rate": integer_or_none(heart_rate.get("average")),
        "maximum_heart_rate": integer_or_none(heart_rate.get("maximum")),
        "calories": integer_or_none(payload.get("calories")),
        "training_load": number_or_none(payload.get("training_load")),
        "raw_payload_id": raw_payload.id,
    }
    if existing is None:
        session.add(PolarTrainingSession(external_id=external_id, **values))
        return "inserted"
    for key, value in values.items():
        setattr(existing, key, value)
    return "updated"


def number_or_none(value: object) -> float | None:
    return float(value) if isinstance(value, (int, float)) else None


def integer_or_none(value: object) -> int | None:
    return value if isinstance(value, int) else None
