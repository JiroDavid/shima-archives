from collections.abc import Callable
from typing import Any

from fastapi.testclient import TestClient

from app.main import app
from app.services.twitch import get_twitch_client

SAMPLE_USER = {
    "id": "12345",
    "login": "yugi2x",
    "display_name": "Yugi2x",
    "broadcaster_type": "partner",
    "description": "card games",
    "profile_image_url": "https://example.com/yugi.png",
    "created_at": "2018-01-01T00:00:00Z",
}

SAMPLE_CLIP = {
    "id": "clip1",
    "url": "https://clips.twitch.tv/clip1",
    "broadcaster_id": "12345",
    "creator_id": "999",
    "creator_name": "Bob",
    "video_id": "987654",
    "game_id": "509658",
    "title": "great play",
    "view_count": 42,
    "created_at": "2024-01-01T00:00:00Z",
    "thumbnail_url": "https://example.com/clip-thumb.png",
    "duration": 30.0,
}


class FakeTwitchClient:
    def __init__(
        self, user: dict[str, Any] | None, clips: list[dict[str, Any]] | None = None
    ) -> None:
        self._user = user
        self._clips = clips or []
        self.captured_filters: dict[str, str | None] = {}

    async def get_user(self, username: str) -> dict[str, Any] | None:
        return self._user

    async def get_clips(
        self,
        broadcaster_id: str,
        game_id: str | None = None,
        started_at: str | None = None,
        ended_at: str | None = None,
    ) -> list[dict[str, Any]]:
        self.captured_filters = {
            "broadcaster_id": broadcaster_id,
            "game_id": game_id,
            "started_at": started_at,
            "ended_at": ended_at,
        }
        return self._clips


def _override(fake: FakeTwitchClient) -> Callable[[], FakeTwitchClient]:
    def factory() -> FakeTwitchClient:
        return fake

    return factory


def test_list_clips_returns_clips() -> None:
    fake = FakeTwitchClient(SAMPLE_USER, [SAMPLE_CLIP])
    app.dependency_overrides[get_twitch_client] = _override(fake)
    try:
        client = TestClient(app)
        response = client.get("/api/v1/channel/yugi2x/clips")
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["id"] == "clip1"
        assert body[0]["title"] == "great play"
        assert body[0]["creator_name"] == "Bob"
        assert body[0]["duration_seconds"] == 30.0
        assert body[0]["game_id"] == "509658"
        assert fake.captured_filters["broadcaster_id"] == "12345"
    finally:
        app.dependency_overrides.clear()


def test_list_clips_returns_empty_list_when_none() -> None:
    fake = FakeTwitchClient(SAMPLE_USER, [])
    app.dependency_overrides[get_twitch_client] = _override(fake)
    try:
        client = TestClient(app)
        response = client.get("/api/v1/channel/yugi2x/clips")
        assert response.status_code == 200
        assert response.json() == []
    finally:
        app.dependency_overrides.clear()


def test_list_clips_returns_404_when_channel_not_found() -> None:
    fake = FakeTwitchClient(None)
    app.dependency_overrides[get_twitch_client] = _override(fake)
    try:
        client = TestClient(app)
        response = client.get("/api/v1/channel/ghost/clips")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_list_clips_passes_through_filters() -> None:
    fake = FakeTwitchClient(SAMPLE_USER, [])
    app.dependency_overrides[get_twitch_client] = _override(fake)
    try:
        client = TestClient(app)
        response = client.get(
            "/api/v1/channel/yugi2x/clips",
            params={"game": "509658", "from": "2024-01-01", "to": "2024-02-01"},
        )
        assert response.status_code == 200
        assert fake.captured_filters == {
            "broadcaster_id": "12345",
            "game_id": "509658",
            "started_at": "2024-01-01",
            "ended_at": "2024-02-01",
        }
    finally:
        app.dependency_overrides.clear()


def test_list_clips_sorted_by_date_orders_newest_first() -> None:
    older = {**SAMPLE_CLIP, "id": "clip-old", "created_at": "2023-01-01T00:00:00Z"}
    newer = {**SAMPLE_CLIP, "id": "clip-new", "created_at": "2024-06-01T00:00:00Z"}
    fake = FakeTwitchClient(SAMPLE_USER, [older, newer])
    app.dependency_overrides[get_twitch_client] = _override(fake)
    try:
        client = TestClient(app)
        response = client.get(
            "/api/v1/channel/yugi2x/clips", params={"sort": "date"}
        )
        assert response.status_code == 200
        body = response.json()
        assert [c["id"] for c in body] == ["clip-new", "clip-old"]
    finally:
        app.dependency_overrides.clear()
