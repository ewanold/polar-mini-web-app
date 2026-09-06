import json
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest
from cryptography.fernet import Fernet

from polar_app.config import Settings
from polar_app.main import create_app
from polar_app.models.base import Base
from polar_app.models.polar import PolarOAuthToken


@pytest.mark.anyio
async def test_connect_redirects_to_polar_with_state_cookie(tmp_path) -> None:
    app = create_app(
        Settings(
            database_path=tmp_path / "polar.sqlite3",
            polar_client_id="client-id",
            polar_client_secret="client-secret",
            polar_redirect_uri="http://localhost:8000/api/polar/callback",
            polar_token_encryption_key=Fernet.generate_key().decode(),
        )
    )
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/polar/connect", follow_redirects=False)

    assert response.status_code == 307
    query = parse_qs(urlsplit(response.headers["location"]).query)
    assert urlsplit(response.headers["location"]).scheme == "https"
    assert urlsplit(response.headers["location"]).netloc == "flow.polar.com"
    assert urlsplit(response.headers["location"]).path == "/oauth2/authorization"
    assert query["response_type"] == ["code"]
    assert query["client_id"] == ["client-id"]
    assert query["redirect_uri"] == ["http://localhost:8000/api/polar/callback"]
    assert query["scope"] == ["accesslink.read_all"]
    assert len(query["state"][0]) >= 32
    assert "polar_oauth_state" in response.headers["set-cookie"]


@pytest.mark.anyio
async def test_callback_exchanges_registers_and_persists_encrypted_token(tmp_path) -> None:
    encryption_key = Fernet.generate_key().decode()

    def polar_responses(request: httpx.Request) -> httpx.Response:
        if request.url == httpx.URL("https://polarremote.com/v2/oauth2/token"):
            assert request.method == "POST"
            assert request.headers["authorization"] == "Basic Y2xpZW50LWlkOmNsaWVudC1zZWNyZXQ="
            assert request.content == (
                b"grant_type=authorization_code&code=one-time-code&"
                b"redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fapi%2Fpolar%2Fcallback"
            )
            return httpx.Response(
                200,
                json={
                    "access_token": "access-token",
                    "token_type": "bearer",
                    "expires_in": 31535999,
                    "x_user_id": 12345,
                },
            )
        if request.url == httpx.URL("https://www.polaraccesslink.com/v3/users"):
            assert request.headers["authorization"] == "Bearer access-token"
            assert json.loads(request.content) == {"member-id": "polar-12345"}
            return httpx.Response(200, json={"polar-user-id": 12345})
        return httpx.Response(404)

    app = create_app(
        Settings(
            database_path=tmp_path / "polar.sqlite3",
            polar_client_id="client-id",
            polar_client_secret="client-secret",
            polar_redirect_uri="http://localhost:8000/api/polar/callback",
            polar_token_encryption_key=encryption_key,
        ),
        polar_transport=httpx.MockTransport(polar_responses),
    )
    Base.metadata.create_all(app.state.engine)
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        connect_response = await client.get("/api/polar/connect", follow_redirects=False)
        state = parse_qs(urlsplit(connect_response.headers["location"]).query)["state"][0]
        callback_response = await client.get(
            "/api/polar/callback", params={"code": "one-time-code", "state": state}
        )

    assert callback_response.status_code == 200
    assert callback_response.json() == {"status": "connected", "polar_user_id": "12345"}
    with app.state.session_factory() as session:
        token = session.query(PolarOAuthToken).one()
    assert token.polar_user_id == "12345"
    decrypted_token = Fernet(encryption_key.encode()).decrypt(token.encrypted_access_token.encode())
    assert decrypted_token == b"access-token"
