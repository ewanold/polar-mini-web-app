from contextlib import asynccontextmanager
from pathlib import Path
from typing import Final

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from polar_app.api.oauth import router as polar_oauth_router
from polar_app.api.sync import router as polar_sync_router
from polar_app.api.timeline import router as timeline_router
from polar_app.api.training_groups import router as training_groups_router
from polar_app.config import Settings
from polar_app.db import create_session_factory, create_sqlite_engine
from polar_app.scheduler import PolarScheduler

APPLICATION_VERSION: Final = "0.1.0"
SCHEMA_VERSION: Final = "0008"
STATIC_DIRECTORY: Final = Path(__file__).resolve().parent / "static"


def create_app(
    settings: Settings | None = None, polar_transport: httpx.AsyncBaseTransport | None = None
) -> FastAPI:
    app_settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.scheduler.start()
        yield
        app.state.scheduler.shutdown()

    app = FastAPI(title="Polar App", version=APPLICATION_VERSION, lifespan=lifespan)
    app.state.settings = app_settings
    app.state.engine = create_sqlite_engine(app_settings)
    app.state.session_factory = create_session_factory(app.state.engine)
    app.state.polar_transport = polar_transport
    app.state.scheduler = PolarScheduler(app.state.session_factory, app_settings, polar_transport)

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "application_version": APPLICATION_VERSION,
            "schema_version": SCHEMA_VERSION,
        }

    app.include_router(polar_oauth_router)
    app.include_router(polar_sync_router)
    app.include_router(timeline_router)
    app.include_router(training_groups_router)

    index_file = STATIC_DIRECTORY / "index.html"
    assets_directory = STATIC_DIRECTORY / "assets"
    if index_file.is_file():
        if assets_directory.is_dir():
            app.mount("/assets", StaticFiles(directory=assets_directory), name="frontend-assets")

        @app.get("/{path:path}", include_in_schema=False)
        def frontend(path: str) -> FileResponse:
            if path == "api" or path.startswith("api/"):
                raise HTTPException(status_code=404, detail="API endpoint not found")
            return FileResponse(index_file)

    return app


app = create_app()
