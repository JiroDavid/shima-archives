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

    async def get_videos(
        self, user_id: str, video_type: str = "archive"
    ) -> list[dict[str, Any]]:
        """Fetch all of a channel's videos, following pagination cursors.

        Defaults to ``archive`` (past broadcasts / VODs, including unlisted ones
        the token can see).
        """
        token = await self._ensure_app_token()
        headers = {
            "Client-Id": settings.twitch_client_id,
            "Authorization": f"Bearer {token}",
        }
        videos: list[dict[str, Any]] = []
        cursor: str | None = None
        while True:
            params: dict[str, str] = {
                "user_id": user_id,
                "type": video_type,
                "first": "100",
            }
            if cursor is not None:
                params["after"] = cursor
            response = await self._client.get(
                "/videos", params=params, headers=headers
            )
            response.raise_for_status()
            payload = response.json()
            videos.extend(payload.get("data", []))
            cursor = payload.get("pagination", {}).get("cursor")
            if not cursor:
                break
        return videos

    async def get_video(self, vod_id: str) -> dict[str, Any] | None:
        """Fetch a single video's metadata by id, or None if it does not exist."""
        token = await self._ensure_app_token()
        response = await self._client.get(
            "/videos",
            params={"id": vod_id},
            headers={
                "Client-Id": settings.twitch_client_id,
                "Authorization": f"Bearer {token}",
            },
        )
        response.raise_for_status()
        data: list[dict[str, Any]] = response.json().get("data", [])
        return data[0] if data else None

    async def get_clips(
        self,
        broadcaster_id: str,
        game_id: str | None = None,
        started_at: str | None = None,
        ended_at: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch a broadcaster's clips, following pagination cursors.

        ``game_id``, ``started_at``, and ``ended_at`` are optional Helix
        filters; omitted when not provided.
        """
        token = await self._ensure_app_token()
        headers = {
            "Client-Id": settings.twitch_client_id,
            "Authorization": f"Bearer {token}",
        }
        clips: list[dict[str, Any]] = []
        cursor: str | None = None
        while True:
            params: dict[str, str] = {"broadcaster_id": broadcaster_id, "first": "100"}
            if game_id is not None:
                params["game_id"] = game_id
            if started_at is not None:
                params["started_at"] = started_at
            if ended_at is not None:
                params["ended_at"] = ended_at
            if cursor is not None:
                params["after"] = cursor
            response = await self._client.get("/clips", params=params, headers=headers)
            response.raise_for_status()
            payload = response.json()
            clips.extend(payload.get("data", []))
            cursor = payload.get("pagination", {}).get("cursor")
            if not cursor:
                break
        return clips

    async def get_vod_comments(self, vod_id: str) -> list[dict[str, Any]]:
        """Fetch a VOD's full chat replay, following the comment cursor.

        Uses the unofficial-but-stable ``/videos/{id}/comments`` endpoint;
        pages via the ``_next`` cursor until exhausted.
        """
        token = await self._ensure_app_token()
        headers = {
            "Client-Id": settings.twitch_client_id,
            "Authorization": f"Bearer {token}",
        }
        comments: list[dict[str, Any]] = []
        cursor: str | None = None
        while True:
            params = {"cursor": cursor} if cursor is not None else {}
            response = await self._client.get(
                f"/videos/{vod_id}/comments", params=params, headers=headers
            )
            response.raise_for_status()
            payload = response.json()
            comments.extend(payload.get("comments", []))
            cursor = payload.get("_next")
            if not cursor:
                break
        return comments

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
