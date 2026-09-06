from pathlib import Path

import httpx
import pytest

import polar_app.main as main_module
from polar_app.main import APPLICATION_VERSION, SCHEMA_VERSION, create_app


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.anyio
async def test_health_reports_service_and_versions() -> None:
    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "application_version": APPLICATION_VERSION,
        "schema_version": SCHEMA_VERSION,
    }


def test_module_exports_runnable_asgi_application() -> None:
    assert isinstance(main_module.app, main_module.FastAPI)


@pytest.mark.anyio
async def test_compiled_frontend_is_served_for_spa_routes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    static_directory = tmp_path / "static"
    static_directory.mkdir()
    (static_directory / "index.html").write_text(
        "<!doctype html><title>Polar test shell</title>", encoding="utf-8"
    )
    monkeypatch.setattr(main_module, "STATIC_DIRECTORY", static_directory)

    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/training")

    assert response.status_code == 200
    assert "Polar test shell" in response.text
