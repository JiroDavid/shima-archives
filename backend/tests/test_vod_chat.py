from collections.abc import Callable
from typing import Any

from fastapi.testclient import TestClient

from app.main import app
from app.services.twitch import get_twitch_client

SAMPLE_COMMENT = {
    "_id": "abc",
    "created_at": "2024-01-01T00:00:12Z",
    "content_offset_seconds": 12.5,
    "commenter": {"display_name": "Bob", "name": "bob"},
    "message": {"body": "LUL chat went crazy", "user_color": "#FF0000"},
}


class FakeTwitchClient:
    def __init__(self, comments: list[dict[str, Any]]) -> None:
        self._comments = comments

    async def get_vod_comments(self, vod_id: str) -> list[dict[str, Any]]:
        return self._comments


def _override(comments: list[dict[str, Any]]) -> Callable[[], FakeTwitchClient]:
    def factory() -> FakeTwitchClient:
        return FakeTwitchClient(comments)

    return factory


def test_get_vod_chat_returns_comments() -> None:
    app.dependency_overrides[get_twitch_client] = _override([SAMPLE_COMMENT])
    try:
        client = TestClient(app)
        response = client.get("/api/v1/vod/987654/chat")
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["username"] == "Bob"
        assert body[0]["message"] == "LUL chat went crazy"
        assert body[0]["offset_seconds"] == 12.5
        assert body[0]["color"] == "#FF0000"
    finally:
        app.dependency_overrides.clear()


def test_get_vod_chat_returns_empty_list_when_none() -> None:
    app.dependency_overrides[get_twitch_client] = _override([])
    try:
        client = TestClient(app)
        response = client.get("/api/v1/vod/987654/chat")
        assert response.status_code == 200
        assert response.json() == []
    finally:
        app.dependency_overrides.clear()
