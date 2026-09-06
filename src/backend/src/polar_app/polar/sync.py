# ruff: noqa: E501

from collections.abc import Callable
from datetime import date, timedelta
from typing import Any

import httpx
from sqlalchemy.orm import Session, sessionmaker

from polar_app.config import Settings
from polar_app.models.polar import PolarOAuthToken
from polar_app.polar.client import PolarClient
from polar_app.polar.sync_daily import (
    sync_activity,
    sync_continuous_heart_rate,
    sync_nightly_recharge,
    sync_sleep,
)
from polar_app.polar.sync_training import sync_training


def connection_status(session: Session) -> dict[str, Any]:
    token = session.query(PolarOAuthToken).one_or_none()
    return {
        "connected": token is not None,
        "polar_user_id": token.polar_user_id if token else None,
        "expires_at": token.expires_at.isoformat() if token and token.expires_at else None,
    }


async def synchronize(
    session_factory: sessionmaker[Session],
    settings: Settings,
    transport: httpx.AsyncBaseTransport | None = None,
) -> dict[str, Any]:
    with session_factory() as session:
        token = session.query(PolarOAuthToken).one_or_none()
        if token is None:
            return {"connected": False, "categories": {}}
        client = PolarClient(settings, token, transport=transport)
    end = date.today()
    start = end - timedelta(days=27)
    categories: dict[str, Callable[[Session], Any]] = {
        "training": lambda session: sync_training(session, client, timezone=settings.timezone),
        "sleep": lambda session: sync_sleep(session, client),
        "nightly_recharge": lambda session: sync_nightly_recharge(session, client),
        "activity": lambda session: sync_activity(session, client, start, end),
        "continuous_heart_rate": lambda session: sync_continuous_heart_rate(session, client, start, end),
    }
    results: dict[str, Any] = {}
    for category, run_category in categories.items():
        with session_factory() as session:
            try:
                results[category] = await run_category(session)
                session.commit()
            except Exception as error:
                session.rollback()
                results[category] = {"error": str(error)}
    return {"connected": True, "categories": results}
