import asyncio
from datetime import UTC, datetime

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session, sessionmaker

from polar_app.config import Settings
from polar_app.models.sync import PolarSyncState
from polar_app.polar.sync import synchronize


class PolarScheduler:
    def __init__(
        self,
        session_factory: sessionmaker[Session],
        settings: Settings,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._settings = settings
        self._transport = transport
        self._run_lock = asyncio.Lock()
        self._scheduler = AsyncIOScheduler()
        self._scheduler.add_job(
            self.run_once,
            "interval",
            minutes=settings.sync_interval_minutes,
            id="polar-sync",
            max_instances=1,
            coalesce=True,
        )

    def start(self) -> None:
        self._scheduler.start()

    def shutdown(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)

    async def run_once(self) -> None:
        if self._run_lock.locked():
            return
        async with self._run_lock:
            with self._session_factory() as session:
                state = session.get(PolarSyncState, "all")
                if state is None:
                    state = PolarSyncState(category="all")
                    session.add(state)
                state.last_attempt_at = datetime.now(UTC)
                state.last_error = None
                session.commit()
            result = await synchronize(self._session_factory, self._settings, self._transport)
            with self._session_factory() as session:
                state = session.get(PolarSyncState, "all")
                if state is None:
                    return
                state.last_success_at = datetime.now(UTC) if result["connected"] else None
                errors = [
                    name
                    for name, value in result["categories"].items()
                    if isinstance(value, dict) and "error" in value
                ]
                state.last_error = ", ".join(errors) if errors else None
                session.commit()
