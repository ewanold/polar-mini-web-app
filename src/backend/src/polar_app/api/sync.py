# ruff: noqa: E501

from datetime import UTC, datetime

from fastapi import APIRouter, Request, Response, status
from sqlalchemy.orm import Session, sessionmaker

from polar_app.config import Settings
from polar_app.models.polar import PolarOAuthToken
from polar_app.models.sync import PolarSyncState
from polar_app.polar.sync import connection_status, synchronize

router = APIRouter(prefix="/api/polar", tags=["polar"])


def settings(request: Request) -> Settings:
    return request.app.state.settings


def sessions(request: Request) -> sessionmaker[Session]:
    return request.app.state.session_factory


@router.get("/status")
def polar_status(request: Request) -> dict[str, object]:
    with sessions(request)() as session:
        return connection_status(session)


@router.delete("/connection", status_code=status.HTTP_204_NO_CONTENT)
def disconnect_polar(request: Request) -> Response:
    with sessions(request)() as session:
        session.query(PolarOAuthToken).delete()
        session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/sync")
async def sync_polar(request: Request) -> dict[str, object]:
    result = await synchronize(
        sessions(request), settings(request), request.app.state.polar_transport
    )
    errors = [
        name
        for name, value in result["categories"].items()
        if isinstance(value, dict) and "error" in value
    ]
    with sessions(request)() as session:
        state = session.get(PolarSyncState, "all")
        if state is None:
            state = PolarSyncState(category="all")
            session.add(state)
        state.last_attempt_at = datetime.now(UTC)
        state.last_error = ", ".join(errors) if errors else None
        if result["connected"] and not errors:
            state.last_success_at = datetime.now(UTC)
        session.commit()
    return result
