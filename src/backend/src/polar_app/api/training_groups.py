from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from polar_app.aggregation.buckets import (
    Bucket,
    month_buckets,
    recent_day_buckets,
    recent_week_buckets,
)
from polar_app.aggregation.rebuild import rebuild_group_buckets
from polar_app.models.polar import PolarTrainingSession
from polar_app.models.training_aggregates import TrainingAggregate
from polar_app.models.training_groups import MappingState, PolarSportTypeMapping, TrainingGroup

router = APIRouter(prefix="/api/training", tags=["training"])


class TrainingGroupCreate(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=100)]
    slug: Annotated[str, Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=100)]
    color: Annotated[str, Field(pattern=r"^#[0-9a-fA-F]{6}$")]


class TrainingGroupResponse(BaseModel):
    id: int
    name: str
    slug: str
    color: str
    position: int
    enabled: bool


class TrainingGroupDelete(BaseModel):
    disposition: Literal["unmapped", "reassign"]
    replacement_group_id: int | None = None


class TrainingSeriesResponse(BaseModel):
    group: TrainingGroupResponse
    range: Literal["4w", "6m", "all"]
    resolution: Literal["day", "week", "month"]
    timezone: str
    aggregation_method: Literal["arithmetic_mean_per_session"] = "arithmetic_mean_per_session"
    buckets: list["TrainingBucketResponse"]


class TrainingBucketResponse(BaseModel):
    date: date
    end_date: date
    session_count: int
    total_distance_meters: float | None
    average_heart_rate: float | None
    average_pace_seconds_per_kilometer: float | None
    average_duration_seconds: float | None
    average_duration_pace_index: float | None
    average_heart_rate_sample_count: int
    average_pace_sample_count: int
    average_duration_sample_count: int
    average_duration_pace_index_sample_count: int


class TrainingSessionResponse(BaseModel):
    external_id: str
    local_date: date
    sport_type: str
    duration_seconds: int | None
    average_heart_rate: int | None
    average_pace_seconds_per_kilometer: float | None
    duration_pace_index: float | None


class SportTypeMappingResponse(BaseModel):
    sport_type: str
    session_count: int
    state: MappingState
    group_id: int | None


class SportTypeMappingUpdate(BaseModel):
    state: MappingState
    group_id: int | None = None


def sessions(request: Request) -> sessionmaker[Session]:
    return request.app.state.session_factory


def serialize_group(group: TrainingGroup) -> TrainingGroupResponse:
    return TrainingGroupResponse(
        id=group.id,
        name=group.name,
        slug=group.slug,
        color=group.color,
        position=group.position,
        enabled=group.enabled,
    )


@router.get("/groups", response_model=list[TrainingGroupResponse])
def list_groups(request: Request) -> list[TrainingGroupResponse]:
    with sessions(request)() as session:
        groups = (
            session.query(TrainingGroup).order_by(TrainingGroup.position, TrainingGroup.name).all()
        )
        return [serialize_group(group) for group in groups]


@router.post("/groups", response_model=TrainingGroupResponse, status_code=status.HTTP_201_CREATED)
def create_group(payload: TrainingGroupCreate, request: Request) -> TrainingGroupResponse:
    with sessions(request)() as session:
        group = TrainingGroup(name=payload.name, slug=payload.slug, color=payload.color)
        session.add(group)
        try:
            session.commit()
        except IntegrityError as error:
            session.rollback()
            raise HTTPException(
                status_code=409, detail="Training group name or slug already exists"
            ) from error
        session.refresh(group)
        return serialize_group(group)


@router.delete("/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(group_id: int, payload: TrainingGroupDelete, request: Request) -> Response:
    with sessions(request)() as session:
        group = session.get(TrainingGroup, group_id)
        if group is None:
            raise HTTPException(status_code=404, detail="Training group not found")
        replacement_group_id = payload.replacement_group_id
        if payload.disposition == "reassign":
            if replacement_group_id is None:
                raise HTTPException(
                    status_code=422, detail="Reassigning requires a replacement training group"
                )
            if replacement_group_id == group.id:
                raise HTTPException(
                    status_code=422, detail="A training group cannot be its own replacement"
                )
            if session.get(TrainingGroup, replacement_group_id) is None:
                raise HTTPException(status_code=404, detail="Replacement training group not found")
        elif replacement_group_id is not None:
            raise HTTPException(
                status_code=422, detail="Unmapping cannot include a replacement training group"
            )
        mappings = session.query(PolarSportTypeMapping).filter_by(group_id=group.id).all()
        local_dates = [
            local_date
            for (local_date,) in session.query(PolarTrainingSession.local_date)
            .join(
                PolarSportTypeMapping,
                PolarSportTypeMapping.sport_type == PolarTrainingSession.sport_type,
            )
            .filter(PolarSportTypeMapping.group_id == group.id)
            .distinct()
            .all()
        ]
        for mapping in mappings:
            mapping.state = "mapped" if replacement_group_id is not None else "unmapped"
            mapping.group_id = replacement_group_id
        session.flush()
        if replacement_group_id is not None:
            rebuild_group_buckets(
                session,
                group_ids=[replacement_group_id],
                local_dates=local_dates,
                timezone=request.app.state.settings.timezone,
            )
        session.delete(group)
        session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/sport-types", response_model=list[SportTypeMappingResponse])
def list_sport_types(request: Request) -> list[SportTypeMappingResponse]:
    with sessions(request)() as session:
        rows = (
            session.query(
                PolarTrainingSession.sport_type,
                func.count(PolarTrainingSession.id),
                PolarSportTypeMapping.state,
                PolarSportTypeMapping.group_id,
            )
            .outerjoin(
                PolarSportTypeMapping,
                PolarSportTypeMapping.sport_type == PolarTrainingSession.sport_type,
            )
            .group_by(
                PolarTrainingSession.sport_type,
                PolarSportTypeMapping.state,
                PolarSportTypeMapping.group_id,
            )
            .order_by(PolarTrainingSession.sport_type)
            .all()
        )
        return [
            SportTypeMappingResponse(
                sport_type=sport_type,
                session_count=session_count,
                state=state or "unmapped",
                group_id=group_id,
            )
            for sport_type, session_count, state, group_id in rows
        ]


@router.put("/sport-types/{sport_type}", response_model=SportTypeMappingResponse)
def update_sport_type_mapping(
    sport_type: str, payload: SportTypeMappingUpdate, request: Request
) -> SportTypeMappingResponse:
    if (payload.state == "mapped") != (payload.group_id is not None):
        raise HTTPException(
            status_code=422, detail="Mapped sport types require a group; other states do not"
        )
    with sessions(request)() as session:
        session_count = session.query(PolarTrainingSession).filter_by(sport_type=sport_type).count()
        if session_count == 0:
            raise HTTPException(status_code=404, detail="Observed Polar sport type not found")
        if payload.group_id is not None and session.get(TrainingGroup, payload.group_id) is None:
            raise HTTPException(status_code=404, detail="Training group not found")
        mapping = session.get(PolarSportTypeMapping, sport_type)
        previous_group_id = (
            mapping.group_id if mapping is not None and mapping.state == "mapped" else None
        )
        if mapping is None:
            mapping = PolarSportTypeMapping(sport_type=sport_type, state=payload.state)
            session.add(mapping)
        mapping.state = payload.state
        mapping.group_id = payload.group_id
        affected_group_ids = {
            group_id for group_id in (previous_group_id, mapping.group_id) if group_id
        }
        if affected_group_ids:
            local_dates = [
                local_date
                for (local_date,) in session.query(PolarTrainingSession.local_date)
                .filter_by(sport_type=sport_type)
                .all()
            ]
            rebuild_group_buckets(
                session,
                group_ids=affected_group_ids,
                local_dates=local_dates,
                timezone=request.app.state.settings.timezone,
            )
        session.commit()
        return SportTypeMappingResponse(
            sport_type=sport_type,
            session_count=session_count,
            state=mapping.state,
            group_id=mapping.group_id,
        )


@router.get("/groups/{group_id}/series", response_model=TrainingSeriesResponse)
def training_series(
    group_id: int, range: Literal["4w", "6m", "all"], request: Request
) -> TrainingSeriesResponse:
    with sessions(request)() as session:
        group = session.get(TrainingGroup, group_id)
        if group is None:
            raise HTTPException(status_code=404, detail="Training group not found")
        resolution, requested_buckets = requested_series_buckets(
            session, group.id, range, request.app.state.settings.timezone
        )
        aggregates = {
            aggregate.bucket_start: aggregate
            for aggregate in session.query(TrainingAggregate)
            .filter_by(
                group_id=group.id,
                resolution=resolution,
                timezone=request.app.state.settings.timezone,
            )
            .all()
        }
        buckets = [
            serialize_bucket(bucket, aggregates.get(bucket.start)) for bucket in requested_buckets
        ]
        return TrainingSeriesResponse(
            group=serialize_group(group),
            range=range,
            resolution=resolution,
            timezone=request.app.state.settings.timezone,
            buckets=buckets,
        )


@router.get("/groups/{group_id}/sessions", response_model=list[TrainingSessionResponse])
def bucket_sessions(
    group_id: int,
    request: Request,
    start: Annotated[date, Query()],
    end: Annotated[date, Query()],
) -> list[TrainingSessionResponse]:
    if start >= end:
        raise HTTPException(status_code=422, detail="Bucket end must be after its start")
    with sessions(request)() as session:
        if session.get(TrainingGroup, group_id) is None:
            raise HTTPException(status_code=404, detail="Training group not found")
        rows = (
            session.query(PolarTrainingSession)
            .join(
                PolarSportTypeMapping,
                PolarSportTypeMapping.sport_type == PolarTrainingSession.sport_type,
            )
            .filter(
                PolarSportTypeMapping.group_id == group_id,
                PolarSportTypeMapping.state == "mapped",
                PolarTrainingSession.local_date >= start,
                PolarTrainingSession.local_date < end,
            )
            .order_by(PolarTrainingSession.local_date, PolarTrainingSession.started_at)
            .all()
        )
        return [
            TrainingSessionResponse(
                external_id=row.external_id,
                local_date=row.local_date,
                sport_type=row.sport_type,
                duration_seconds=row.duration_seconds,
                average_heart_rate=row.average_heart_rate,
                average_pace_seconds_per_kilometer=row.average_pace_seconds_per_kilometer,
                duration_pace_index=row.duration_pace_index,
            )
            for row in rows
        ]


def requested_series_buckets(
    session: Session, group_id: int, range: Literal["4w", "6m", "all"], timezone: str
) -> tuple[Literal["day", "week", "month"], list[Bucket]]:
    today = date.today()
    if range == "4w":
        return "day", recent_day_buckets(today)
    if range == "6m":
        return "week", recent_week_buckets(today)
    first_bucket = (
        session.query(func.min(TrainingAggregate.bucket_start))
        .filter_by(group_id=group_id, resolution="month", timezone=timezone)
        .scalar()
    )
    return "month", month_buckets(first_bucket, today) if first_bucket else []


def serialize_bucket(bucket: Bucket, aggregate: TrainingAggregate | None) -> TrainingBucketResponse:
    if aggregate is None:
        return TrainingBucketResponse(
            date=bucket.start,
            end_date=bucket.end,
            session_count=0,
            total_distance_meters=None,
            average_heart_rate=None,
            average_pace_seconds_per_kilometer=None,
            average_duration_seconds=None,
            average_duration_pace_index=None,
            average_heart_rate_sample_count=0,
            average_pace_sample_count=0,
            average_duration_sample_count=0,
            average_duration_pace_index_sample_count=0,
        )
    return TrainingBucketResponse(
        date=bucket.start,
        end_date=bucket.end,
        session_count=aggregate.session_count,
        total_distance_meters=aggregate.total_distance_meters,
        average_heart_rate=aggregate.average_heart_rate,
        average_pace_seconds_per_kilometer=aggregate.average_pace_seconds_per_kilometer,
        average_duration_seconds=aggregate.average_duration_seconds,
        average_duration_pace_index=aggregate.average_duration_pace_index,
        average_heart_rate_sample_count=aggregate.average_heart_rate_sample_count,
        average_pace_sample_count=aggregate.average_pace_sample_count,
        average_duration_sample_count=aggregate.average_duration_sample_count,
        average_duration_pace_index_sample_count=aggregate.average_duration_pace_index_sample_count,
    )
