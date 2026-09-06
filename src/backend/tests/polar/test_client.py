import asyncio
from datetime import UTC, datetime

import httpx
import pytest
from cryptography.fernet import Fernet

from polar_app.config import Settings
from polar_app.models.polar import PolarOAuthToken
from polar_app.polar.client import PolarApiError, PolarClient


def test_client_decrypts_token_and_retries_rate_limit(tmp_path) -> None:
    encryption_key = Fernet.generate_key().decode()
    settings = Settings(
        database_path=tmp_path / "polar.sqlite3",
        polar_token_encryption_key=encryption_key,
    )
    encrypted_token = Fernet(encryption_key.encode()).encrypt(b"access-token").decode()
    token = PolarOAuthToken(
        polar_user_id="12345",
        encrypted_access_token=encrypted_token,
        token_type="bearer",
        expires_at=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    responses = [
        httpx.Response(429, headers={"Retry-After": "2"}),
        httpx.Response(200, json={"ok": True}),
    ]
    delays: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer access-token"
        return responses.pop(0)

    async def sleep(delay: float) -> None:
        delays.append(delay)

    client = PolarClient(
        settings,
        token,
        transport=httpx.MockTransport(handler),
        sleep=sleep,
    )

    response = asyncio.run(client.get("/v3/exercises"))

    assert response == {"ok": True}
    assert delays == [2.0]


def test_client_rejects_malformed_success_response(tmp_path) -> None:
    encryption_key = Fernet.generate_key().decode()
    settings = Settings(
        database_path=tmp_path / "polar.sqlite3", polar_token_encryption_key=encryption_key
    )
    token = PolarOAuthToken(
        polar_user_id="12345",
        encrypted_access_token=Fernet(encryption_key.encode()).encrypt(b"access-token").decode(),
        token_type="bearer",
        expires_at=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    client = PolarClient(
        settings,
        token,
        transport=httpx.MockTransport(lambda _: httpx.Response(200, text="nope")),
    )

    with pytest.raises(PolarApiError, match="invalid JSON"):
        asyncio.run(client.get("/v3/exercises"))
