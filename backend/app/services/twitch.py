"""Twitch Helix API client.

All Twitch calls go through the backend (never the frontend). Uses an async
httpx client and a client-credentials app token for public data.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings

HELIX_BASE = "https://api.twitch.tv/helix"
OAUTH_TOKEN_URL = "https://id.twitch.tv/oauth2/token"


class TwitchClient:
    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client or httpx.AsyncClient(base_url=HELIX_BASE, timeout=10.0)
        self._app_token: str | None = None

    async def _ensure_app_token(self) -> str:
        """Fetch (and cache) a client-credentials app access token."""
        if self._app_token is not None:
            return self._app_token
        response = await self._client.post(
            OAUTH_TOKEN_URL,
            data={
                "client_id": settings.twitch_client_id,
                "client_secret": settings.twitch_client_secret,
                "grant_type": "client_credentials",
            },
        )
        response.raise_for_status()
        token: str = response.json()["access_token"]
        self._app_token = token
        return token

    async def get_user(self, username: str) -> dict[str, Any] | None:
        """Resolve a login name to a Twitch user, or None if it does not exist."""
        token = await self._ensure_app_token()
        response = await self._client.get(
            "/users",
            params={"login": username},
            headers={
                "Client-Id": settings.twitch_client_id,
                "Authorization": f"Bearer {token}",
            },
        )
        response.raise_for_status()
        data: list[dict[str, Any]] = response.json().get("data", [])
        return data[0] if data else None

    async def aclose(self) -> None:
        await self._client.aclose()


_client: TwitchClient | None = None


def get_twitch_client() -> TwitchClient:
    """FastAPI dependency: shared TwitchClient instance."""
    global _client
    if _client is None:
        _client = TwitchClient()
    return _client


__all__ = ["TwitchClient", "get_twitch_client", "HELIX_BASE", "OAUTH_TOKEN_URL"]
