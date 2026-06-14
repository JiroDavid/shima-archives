from collections.abc import Callable
from typing import Any

from fastapi.testclient import TestClient

from app.main import app
from app.services.twitch import get_twitch_client

SAMPLE_VIDEO = {
    "id": "987654",
    "user_id": "12345",
    "user_login": "yugi2x",
    "user_name": "Yugi2x",
    "title": "ranked grind",
    "description": "",
    "created_at": "2024-01-01T00:00:00Z",
    "published_at": "2024-01-01T03:00:00Z",
    "url": "https://twitch.tv/videos/987654",
    "thumbnail_url": "https://example.com/thumb.png",
    "viewable": "public",
    "view_count": 100,
    "language": "en",
    "type": "archive",
    "duration": "3h8m33s",
}


class FakeTwitchClient:
    def __init__(self, videos: list[dict[str, Any]]) -> None:
        self._videos = videos

    async def get_videos(
        self, user_id: str, video_type: str = "archive"
    ) -> list[dict[str, Any]]:
        return self._videos


def _override(videos: list[dict[str, Any]]) -> Callable[[], FakeTwitchClient]:
    def factory() -> FakeTwitchClient:
        return FakeTwitchClient(videos)

    return factory


def test_list_vods_returns_videos() -> None:
    app.dependency_overrides[get_twitch_client] = _override([SAMPLE_VIDEO])
    try:
        client = TestClient(app)
        response = client.get("/api/v1/vods/12345")
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["twitch_vod_id"] == "987654"
        assert body[0]["user_id"] == "12345"
        assert body[0]["title"] == "ranked grind"
        assert body[0]["duration"] == "3h8m33s"
        assert body[0]["type"] == "archive"
    finally:
        app.dependency_overrides.clear()


def test_list_vods_returns_empty_list_when_none() -> None:
    app.dependency_overrides[get_twitch_client] = _override([])
    try:
        client = TestClient(app)
        response = client.get("/api/v1/vods/12345")
        assert response.status_code == 200
        assert response.json() == []
    finally:
        app.dependency_overrides.clear()
