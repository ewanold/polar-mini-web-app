from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from urllib.parse import urlencode

import httpx
from cryptography.fernet import Fernet
from sqlalchemy.orm import Session

from polar_app.config import Settings
from polar_app.models.polar import PolarOAuthToken

AUTHORIZATION_ENDPOINT = "https://flow.polar.com/oauth2/authorization"
TOKEN_ENDPOINT = "https://polarremote.com/v2/oauth2/token"
REGISTER_USER_ENDPOINT = "https://www.polaraccesslink.com/v3/users"
OAUTH_SCOPE = "accesslink.read_all"


class PolarOAuthError(Exception):
    pass


def create_authorization_request(settings: Settings) -> tuple[str, str]:
    if not settings.polar_client_id or not settings.polar_client_secret:
        raise ValueError("Polar OAuth client credentials are not configured")
    if not settings.polar_token_encryption_key:
        raise ValueError("Polar token encryption key is not configured")

    state = token_urlsafe(32)
    query = urlencode(
        {
            "response_type": "code",
            "client_id": settings.polar_client_id,
            "redirect_uri": settings.polar_redirect_uri,
            "scope": OAUTH_SCOPE,
            "state": state,
        }
    )
    return f"{AUTHORIZATION_ENDPOINT}?{query}", state


async def connect_authorized_user(
    settings: Settings,
    authorization_code: str,
    session: Session,
    transport: httpx.AsyncBaseTransport | None = None,
) -> str:
    if not settings.polar_client_id or not settings.polar_client_secret:
        raise PolarOAuthError("Polar OAuth client credentials are not configured")
    if not settings.polar_token_encryption_key:
        raise PolarOAuthError("Polar token encryption key is not configured")

    async with httpx.AsyncClient(transport=transport, timeout=httpx.Timeout(15.0)) as client:
        token_response = await client.post(
            TOKEN_ENDPOINT,
            auth=(settings.polar_client_id, settings.polar_client_secret.get_secret_value()),
            data={
                "grant_type": "authorization_code",
                "code": authorization_code,
                "redirect_uri": settings.polar_redirect_uri,
            },
            headers={"Accept": "application/json;charset=UTF-8"},
        )
        if token_response.is_error:
            raise PolarOAuthError("Polar rejected the authorization code")
        token_payload = token_response.json()
        try:
            access_token = token_payload["access_token"]
            token_type = token_payload["token_type"]
            polar_user_id = str(token_payload["x_user_id"])
        except (KeyError, TypeError) as error:
            raise PolarOAuthError("Polar returned an invalid token response") from error
        if not all(isinstance(value, str) for value in (access_token, token_type, polar_user_id)):
            raise PolarOAuthError("Polar returned an invalid token response")

        registration_response = await client.post(
            REGISTER_USER_ENDPOINT,
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
            json={"member-id": f"polar-{polar_user_id}"},
        )
        if registration_response.status_code not in {200, 409}:
            raise PolarOAuthError("Polar could not register the user")

    expires_in = token_payload.get("expires_in")
    expires_at = (
        datetime.now(UTC) + timedelta(seconds=expires_in)
        if isinstance(expires_in, int) and expires_in > 0
        else None
    )
    now = datetime.now(UTC)
    token_cipher = Fernet(settings.polar_token_encryption_key.get_secret_value().encode())
    encrypted_access_token = token_cipher.encrypt(access_token.encode()).decode()
    stored_token = (
        session.query(PolarOAuthToken).filter_by(polar_user_id=polar_user_id).one_or_none()
    )
    if stored_token is None:
        stored_token = PolarOAuthToken(
            polar_user_id=polar_user_id,
            encrypted_access_token=encrypted_access_token,
            token_type=token_type,
            expires_at=expires_at,
            created_at=now,
            updated_at=now,
        )
        session.add(stored_token)
    else:
        stored_token.encrypted_access_token = encrypted_access_token
        stored_token.token_type = token_type
        stored_token.expires_at = expires_at
        stored_token.updated_at = now
    session.commit()
    return polar_user_id
