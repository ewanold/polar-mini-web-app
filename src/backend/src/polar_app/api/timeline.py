from datetime import date, datetime, time, timedelta
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session, sessionmaker

from polar_app.models.polar import (
    PolarActivityDay,
    PolarHeartRateSample,
    PolarNightlyRecharge,
    PolarSleepDay,
    TimelineEvent,
)

router = APIRouter(prefix="/api/timeline", tags=["timeline"])


class TimelineSleepResponse(BaseModel):
    duration_seconds: int | None
    score: int | None
    start_time: datetime | None
    end_time: datetime | None


class TimelineActivityResponse(BaseModel):
    active_steps: int | None
    active_calories: int | None


class TimelineHeartRateSampleResponse(BaseModel):
    sampled_at: datetime
    heart_rate: int


class TimelineHeartRateResponse(BaseModel):
    average: int
    minimum: int
    maximum: int
    samples: list[TimelineHeartRateSampleResponse]


class TimelineNightlyRechargeResponse(BaseModel):
    heart_rate_avg: int | None
    heart_rate_variability_avg: int | None
    breathing_rate_avg: float | None
    ans_charge: float | None
    nightly_recharge_status: int | None


class TimelineEventResponse(BaseModel):
    id: int
    date: date
    description: str


class TimelineEventCreate(BaseModel):
    date: date
    description: str


class TimelineEventUpdate(BaseModel):
    description: str


class TimelineDayResponse(BaseModel):
    date: date
    sleep: TimelineSleepResponse | None
    activity: TimelineActivityResponse | None
    nightly_recharge: TimelineNightlyRechargeResponse | None
    heart_rate: TimelineHeartRateResponse | None
    events: list[TimelineEventResponse]


class TimelineResponse(BaseModel):
    start: date
    end: date
    days: list[TimelineDayResponse]


def sessions(request: Request) -> sessionmaker[Session]:
    return request.app.state.session_factory


@router.post("/events", response_model=TimelineEventResponse, status_code=201)
def create_timeline_event(payload: TimelineEventCreate, request: Request) -> TimelineEventResponse:
    description = payload.description.strip()
    if not description:
        raise HTTPException(status_code=422, detail="Timeline event description must not be blank")
    with sessions(request)() as session:
        event = TimelineEvent(event_date=payload.date, description=description)
        session.add(event)
        session.commit()
        session.refresh(event)
        return TimelineEventResponse(
            id=event.id, date=event.event_date, description=event.description
        )


@router.put("/events/{event_id}", response_model=TimelineEventResponse)
def update_timeline_event(
    event_id: int, payload: TimelineEventUpdate, request: Request
) -> TimelineEventResponse:
    description = payload.description.strip()
    if not description:
        raise HTTPException(status_code=422, detail="Timeline event description must not be blank")
    with sessions(request)() as session:
        event = session.get(TimelineEvent, event_id)
        if event is None:
            raise HTTPException(status_code=404, detail="Timeline event was not found")
        event.description = description
        session.commit()
        session.refresh(event)
        return TimelineEventResponse(
            id=event.id, date=event.event_date, description=event.description
        )


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_timeline_event(event_id: int, request: Request) -> Response:
    with sessions(request)() as session:
        event = session.get(TimelineEvent, event_id)
        if event is None:
            raise HTTPException(status_code=404, detail="Timeline event was not found")
        session.delete(event)
        session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("", response_model=TimelineResponse)
def timeline(
    request: Request,
    start: Annotated[date | None, Query()] = None,
    end: Annotated[date | None, Query()] = None,
) -> TimelineResponse:
    if (start is None) != (end is None):
        raise HTTPException(
            status_code=422,
            detail="Timeline start and end must be provided together",
        )
    if start is None and end is None:
        with sessions(request)() as session:
            latest_sleep = session.query(func.max(PolarSleepDay.sleep_date)).scalar()
            latest_activity = session.query(func.max(PolarActivityDay.activity_date)).scalar()
            latest_sample = (
                session.query(PolarHeartRateSample)
                .order_by(PolarHeartRateSample.sampled_at.desc())
                .first()
            )
        available_dates = [
            value for value in (latest_sleep, latest_activity) if value is not None
        ]
        if latest_sample is not None:
            available_dates.append(latest_sample.sampled_at.date())
        end = max(available_dates, default=date.today())
        start = end - timedelta(days=27)
    assert start is not None and end is not None
    if end < start:
        raise HTTPException(status_code=422, detail="Timeline end must not precede its start")
    if (end - start).days >= 31:
        raise HTTPException(status_code=422, detail="Timeline requests may span at most 31 days")

    with sessions(request)() as session:
        sleep_days = {
            row.sleep_date: TimelineSleepResponse(
                duration_seconds=row.duration_seconds,
                score=row.score,
                start_time=row.start_time,
                end_time=row.end_time,
            )
            for row in session.query(PolarSleepDay)
            .filter(PolarSleepDay.sleep_date >= start, PolarSleepDay.sleep_date <= end)
            .all()
        }
        activity_days = {
            row.activity_date: TimelineActivityResponse(
                active_steps=row.active_steps,
                active_calories=row.active_calories,
            )
            for row in session.query(PolarActivityDay)
            .filter(PolarActivityDay.activity_date >= start, PolarActivityDay.activity_date <= end)
            .all()
        }
        nightly_recharges = {
            row.recharge_date: TimelineNightlyRechargeResponse(
                heart_rate_avg=row.nightly_heart_rate_avg,
                heart_rate_variability_avg=row.heart_rate_variability_avg,
                breathing_rate_avg=row.breathing_rate_avg,
                ans_charge=row.ans_charge,
                nightly_recharge_status=row.nightly_recharge_status,
            )
            for row in session.query(PolarNightlyRecharge)
            .filter(
                PolarNightlyRecharge.recharge_date >= start,
                PolarNightlyRecharge.recharge_date <= end,
            )
            .all()
        }
        events_by_date: dict[date, list[TimelineEventResponse]] = {}
        for event in session.query(TimelineEvent).filter(
            TimelineEvent.event_date >= start, TimelineEvent.event_date <= end
        ).order_by(TimelineEvent.event_date, TimelineEvent.id).all():
            events_by_date.setdefault(event.event_date, []).append(
                TimelineEventResponse(
                    id=event.id, date=event.event_date, description=event.description
                )
            )
        sample_start = datetime.combine(start, time.min)
        sample_end = datetime.combine(end + timedelta(days=1), time.min)
        samples_by_date: dict[date, list[TimelineHeartRateSampleResponse]] = {}
        for row in (
            session.query(PolarHeartRateSample)
            .filter(
                PolarHeartRateSample.sampled_at >= sample_start,
                PolarHeartRateSample.sampled_at < sample_end,
            )
            .order_by(PolarHeartRateSample.sampled_at)
            .all()
        ):
            samples_by_date.setdefault(row.sampled_at.date(), []).append(
                TimelineHeartRateSampleResponse(
                    sampled_at=row.sampled_at, heart_rate=row.heart_rate
                )
            )

    days = []
    current_date = start
    while current_date <= end:
        heart_rate_samples = samples_by_date.get(current_date, [])
        heart_rate = None
        if heart_rate_samples:
            values = [sample.heart_rate for sample in heart_rate_samples]
            heart_rate = TimelineHeartRateResponse(
                average=round(sum(values) / len(values)),
                minimum=min(values),
                maximum=max(values),
                samples=heart_rate_samples,
            )
        days.append(
            TimelineDayResponse(
                date=current_date,
                sleep=sleep_days.get(current_date),
                activity=activity_days.get(current_date),
                nightly_recharge=nightly_recharges.get(current_date),
                heart_rate=heart_rate,
                events=events_by_date.get(current_date, []),
            )
        )
        current_date += timedelta(days=1)
    return TimelineResponse(start=start, end=end, days=days)
