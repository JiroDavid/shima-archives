"""Twitch Helix API client.

All Twitch calls go through the backend (never the frontend). Uses an async
httpx client and a client-credentials app token for public data. Methods are
skeletons to be implemented alongside their endpoints.
"""

from __future__ import annotations

import httpx

HELIX_BASE = "https://api.twitch.tv/helix"
OAUTH_TOKEN_URL = "https://id.twitch.tv/oauth2/token"


class TwitchClient:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(base_url=HELIX_BASE, timeout=10.0)
        self._app_token: str | None = None

    async def _ensure_app_token(self) -> str:
        """Fetch (and cache) a client-credentials app access token."""
        raise NotImplementedError

    async def get_user(self, username: str) -> dict[str, object]:
        """Resolve a login name to a Twitch user (id, display name, etc.)."""
        raise NotImplementedError

    async def aclose(self) -> None:
        await self._client.aclose()


__all__ = ["TwitchClient", "HELIX_BASE", "OAUTH_TOKEN_URL"]
