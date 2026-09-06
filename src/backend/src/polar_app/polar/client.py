import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any

import httpx
from cryptography.fernet import Fernet, InvalidToken

from polar_app.config import Settings
from polar_app.models.polar import PolarOAuthToken

API_BASE_URL = "https://www.polaraccesslink.com"
MAX_ATTEMPTS = 3


class PolarApiError(Exception):
    pass


class PolarClient:
    def __init__(
        self,
        settings: Settings,
        token: PolarOAuthToken,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        if not settings.polar_token_encryption_key:
            raise PolarApiError("Polar token encryption key is not configured")
        try:
            self._access_token = Fernet(
                settings.polar_token_encryption_key.get_secret_value().encode()
            ).decrypt(token.encrypted_access_token.encode()).decode()
        except (InvalidToken, UnicodeDecodeError) as error:
            raise PolarApiError("stored Polar token cannot be decrypted") from error
        self._transport = transport
        self._sleep = sleep

    async def get(self, path: str, params: dict[str, str] | None = None) -> Any:
        if not path.startswith("/"):
            raise ValueError("Polar API paths must begin with a slash")
        async with httpx.AsyncClient(
            base_url=API_BASE_URL,
            transport=self._transport,
            timeout=httpx.Timeout(connect=5.0, read=15.0, write=15.0, pool=5.0),
        ) as client:
            for attempt in range(MAX_ATTEMPTS):
                try:
                    response = await client.get(
                        path,
                        params=params,
                        headers={"Authorization": f"Bearer {self._access_token}"},
                    )
                except httpx.TransportError as error:
                    if attempt == MAX_ATTEMPTS - 1:
                        raise PolarApiError("Polar request failed") from error
                    await self._sleep(float(2**attempt))
                    continue

                if response.status_code == 401:
                    raise PolarApiError("Polar access token was rejected")
                if response.status_code == 429 or 500 <= response.status_code < 600:
                    if attempt == MAX_ATTEMPTS - 1:
                        raise PolarApiError(
                            f"Polar request failed with HTTP {response.status_code}"
                        )
                    await self._sleep(self._retry_delay(response, attempt))
                    continue
                if response.is_error:
                    raise PolarApiError(f"Polar request failed with HTTP {response.status_code}")
                try:
                    return response.json()
                except ValueError as error:
                    raise PolarApiError("Polar returned invalid JSON") from error
        raise AssertionError("unreachable")

    @staticmethod
    def _retry_delay(response: httpx.Response, attempt: int) -> float:
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return max(0.0, float(retry_after))
            except ValueError:
                try:
                    retry_at = parsedate_to_datetime(retry_after)
                    if retry_at.tzinfo is None:
                        retry_at = retry_at.replace(tzinfo=UTC)
                    return max(0.0, (retry_at - datetime.now(UTC)).total_seconds())
                except (TypeError, ValueError):
                    pass
        return float(2**attempt)
