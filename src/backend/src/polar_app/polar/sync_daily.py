# ruff: noqa: E501

import hashlib
import json
from datetime import UTC, date, datetime
from typing import Any, Protocol

from sqlalchemy.orm import Session

from polar_app.models.polar import (
    PolarActivityDay,
    PolarHeartRateSample,
    PolarNightlyRecharge,
    PolarRawPayload,
    PolarSleepDay,
)


class DailyClient(Protocol):
    async def get(self, path: str, params: dict[str, str] | None = None) -> object: ...


async def sync_sleep(session: Session, client: DailyClient) -> dict[str, int]:
    response = await client.get("/v3/users/sleep")
    nights = response.get("nights", []) if isinstance(response, dict) else []
    return _sync_rows(session, nights, "/v3/users/sleep", _upsert_sleep)


async def sync_nightly_recharge(session: Session, client: DailyClient) -> dict[str, int]:
    response = await client.get("/v3/users/nightly-recharge")
    recharges = response.get("recharges", []) if isinstance(response, dict) else []
    return _sync_rows(session, recharges, "/v3/users/nightly-recharge", _upsert_recharge)


async def sync_activity(session: Session, client: DailyClient, start: date, end: date) -> dict[str, int]:
    rows = await client.get(
        "/v3/users/activities", params={"from": start.isoformat(), "to": end.isoformat()}
    )
    return _sync_rows(session, rows if isinstance(rows, list) else [], "/v3/users/activities", _upsert_activity)


async def sync_continuous_heart_rate(
    session: Session, client: DailyClient, start: date, end: date
) -> dict[str, int]:
    response = await client.get(
        "/v3/users/continuous-heart-rate", params={"from": start.isoformat(), "to": end.isoformat()}
    )
    rows = response.get("heart_rates", []) if isinstance(response, dict) else response
    result = {"inserted": 0, "updated": 0, "skipped": 0, "errors": 0}
    for day in rows if isinstance(rows, list) else []:
        if not isinstance(day, dict):
            result["errors"] += 1
            continue
        try:
            day_date = date.fromisoformat(required_string(day, "date"))
            raw, _ = _raw_payload(session, "/v3/users/continuous-heart-rate", day_date.isoformat(), day)
            samples = day.get("heart_rate_samples", [])
            if not isinstance(samples, list):
                raise ValueError("heart_rate_samples must be a list")
            for sample in samples:
                if not isinstance(sample, dict):
                    continue
                sampled_at = datetime.fromisoformat(
                    f"{day_date.isoformat()}T{required_string(sample, 'sample_time')}"
                )
                heart_rate = integer_or_none(sample.get("heart_rate"))
                if heart_rate is None:
                    continue
                existing = session.query(PolarHeartRateSample).filter_by(sampled_at=sampled_at).one_or_none()
                if existing is None:
                    session.add(
                        PolarHeartRateSample(
                            sampled_at=sampled_at, heart_rate=heart_rate, raw_payload_id=raw.id
                        )
                    )
                    result["inserted"] += 1
                elif existing.heart_rate == heart_rate:
                    result["skipped"] += 1
                else:
                    existing.heart_rate = heart_rate
                    existing.raw_payload_id = raw.id
                    result["updated"] += 1
        except (TypeError, ValueError):
            result["errors"] += 1
    return result


def _sync_rows(
    session: Session,
    rows: object,
    endpoint: str,
    upsert: Any,
) -> dict[str, int]:
    result = {"inserted": 0, "updated": 0, "skipped": 0, "errors": 0}
    if not isinstance(rows, list):
        return result | {"errors": 1}
    for row in rows:
        if not isinstance(row, dict):
            result["errors"] += 1
            continue
        try:
            result[upsert(session, row, endpoint)] += 1
        except (TypeError, ValueError):
            result["errors"] += 1
    return result


def _raw_payload(session: Session, endpoint: str, external_id: str, payload: dict[str, Any]) -> tuple[PolarRawPayload, bool]:
    content_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    raw = session.query(PolarRawPayload).filter_by(endpoint=endpoint, external_id=external_id).one_or_none()
    if raw and raw.content_hash == content_hash:
        return raw, False
    if raw is None:
        raw = PolarRawPayload(
            endpoint=endpoint,
            external_id=external_id,
            fetched_at=datetime.now(UTC),
            payload_json=payload,
            content_hash=content_hash,
        )
        session.add(raw)
        session.flush()
    else:
        raw.fetched_at = datetime.now(UTC)
        raw.payload_json = payload
        raw.content_hash = content_hash
    return raw, True


def _upsert_sleep(session: Session, payload: dict[str, Any], endpoint: str) -> str:
    sleep_date = date.fromisoformat(required_string(payload, "date"))
    raw, changed = _raw_payload(session, endpoint, sleep_date.isoformat(), payload)
    existing = session.query(PolarSleepDay).filter_by(sleep_date=sleep_date).one_or_none()
    if existing and not changed:
        return "skipped"
    values = {
        "start_time": parse_datetime(payload.get("sleep_start_time")),
        "end_time": parse_datetime(payload.get("sleep_end_time")),
        "duration_seconds": sleep_duration(payload),
        "score": integer_or_none(payload.get("sleep_score")),
        "raw_payload_id": raw.id,
    }
    if existing is None:
        session.add(PolarSleepDay(sleep_date=sleep_date, **values))
        return "inserted"
    for key, value in values.items():
        setattr(existing, key, value)
    return "updated"


def _upsert_recharge(session: Session, payload: dict[str, Any], endpoint: str) -> str:
    recharge_date = date.fromisoformat(required_string(payload, "date"))
    raw, changed = _raw_payload(session, endpoint, recharge_date.isoformat(), payload)
    existing = session.query(PolarNightlyRecharge).filter_by(recharge_date=recharge_date).one_or_none()
    if existing and not changed and existing.heart_rate_variability_avg is not None:
        return "skipped"
    values = {
        "status": string_or_none(payload.get("nightly_recharge_status")),
        "ans_charge": float_or_none(payload.get("ans_charge")),
        "ans_charge_status": integer_or_none(payload.get("ans_charge_status")),
        "nightly_recharge_status": integer_or_none(payload.get("nightly_recharge_status")),
        "nightly_heart_rate_avg": integer_or_none(payload.get("heart_rate_avg")),
        "heart_rate_variability_avg": integer_or_none(payload.get("heart_rate_variability_avg")),
        "breathing_rate_avg": float_or_none(payload.get("breathing_rate_avg")),
        "raw_payload_id": raw.id,
    }
    if existing is None:
        session.add(PolarNightlyRecharge(recharge_date=recharge_date, **values))
        return "inserted"
    for key, value in values.items():
        setattr(existing, key, value)
    return "updated"


def _upsert_activity(session: Session, payload: dict[str, Any], endpoint: str) -> str:
    activity_date = date.fromisoformat(required_string(payload, "start_time")[:10])
    raw, changed = _raw_payload(session, endpoint, activity_date.isoformat(), payload)
    existing = session.query(PolarActivityDay).filter_by(activity_date=activity_date).one_or_none()
    if existing and not changed:
        return "skipped"
    values = {
        "active_steps": integer_or_none(payload.get("steps")),
        "active_calories": integer_or_none(payload.get("active_calories")),
        "raw_payload_id": raw.id,
    }
    if existing is None:
        session.add(PolarActivityDay(activity_date=activity_date, **values))
        return "inserted"
    for key, value in values.items():
        setattr(existing, key, value)
    return "updated"


def required_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise ValueError(f"Polar payload field {key} is required")
    return value


def string_or_none(value: object) -> str | None:
    return str(value) if isinstance(value, (str, int)) else None


def integer_or_none(value: object) -> int | None:
    return value if isinstance(value, int) else None


def float_or_none(value: object) -> float | None:
    return float(value) if isinstance(value, (int, float)) else None


def parse_datetime(value: object) -> datetime | None:
    return datetime.fromisoformat(value) if isinstance(value, str) else None


def sleep_duration(payload: dict[str, Any]) -> int | None:
    start = parse_datetime(payload.get("sleep_start_time"))
    end = parse_datetime(payload.get("sleep_end_time"))
    return int((end - start).total_seconds()) if start and end else None
