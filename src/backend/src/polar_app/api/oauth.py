from secrets import compare_digest

import httpx
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session, sessionmaker

from polar_app.config import Settings
from polar_app.polar.oauth import (
    PolarOAuthError,
    connect_authorized_user,
    create_authorization_request,
)

router = APIRouter(prefix="/api/polar", tags=["polar"])


def app_settings(request: Request) -> Settings:
    settings = request.app.state.settings
    if not isinstance(settings, Settings):
        raise RuntimeError("application settings are unavailable")
    return settings


def app_session_factory(request: Request) -> sessionmaker[Session]:
    return request.app.state.session_factory


def app_transport(request: Request) -> httpx.AsyncBaseTransport | None:
    return request.app.state.polar_transport


@router.get("/connect", status_code=307)
def connect_polar(request: Request) -> RedirectResponse:
    settings = app_settings(request)
    try:
        authorization_url, state = create_authorization_request(settings)
    except ValueError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

    response = RedirectResponse(authorization_url, status_code=307)
    response.set_cookie(
        "polar_oauth_state",
        state,
        httponly=True,
        max_age=600,
        samesite="lax",
        secure=settings.polar_redirect_uri.startswith("https://"),
    )
    return response


@router.get("/callback")
async def polar_callback(
    request: Request,
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
) -> JSONResponse:
    expected_state = request.cookies.get("polar_oauth_state")
    if not expected_state or not state or not compare_digest(expected_state, state):
        raise HTTPException(status_code=400, detail="Polar OAuth state validation failed")
    if error:
        raise HTTPException(status_code=400, detail=f"Polar authorization failed: {error}")
    if not code:
        raise HTTPException(status_code=400, detail="Polar authorization code is missing")

    with app_session_factory(request)() as session:
        try:
            polar_user_id = await connect_authorized_user(
                app_settings(request), code, session, app_transport(request)
            )
        except PolarOAuthError as exception:
            session.rollback()
            raise HTTPException(status_code=502, detail=str(exception)) from exception

    response = JSONResponse({"status": "connected", "polar_user_id": polar_user_id})
    response.delete_cookie("polar_oauth_state")
    return response
