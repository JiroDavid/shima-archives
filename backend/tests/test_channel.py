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


class FakeTwitchClient:
    def __init__(self, user: dict[str, Any] | None) -> None:
        self._user = user

    async def get_user(self, username: str) -> dict[str, Any] | None:
        return self._user


def _override(user: dict[str, Any] | None) -> Callable[[], FakeTwitchClient]:
    def factory() -> FakeTwitchClient:
        return FakeTwitchClient(user)

    return factory


def test_get_channel_returns_resolved_info() -> None:
    app.dependency_overrides[get_twitch_client] = _override(SAMPLE_USER)
    try:
        client = TestClient(app)
        response = client.get("/api/v1/channel/yugi2x")
        assert response.status_code == 200
        body = response.json()
        assert body["twitch_id"] == "12345"
        assert body["login"] == "yugi2x"
        assert body["display_name"] == "Yugi2x"
        assert body["broadcaster_type"] == "partner"
    finally:
        app.dependency_overrides.clear()


def test_get_channel_returns_404_when_not_found() -> None:
    app.dependency_overrides[get_twitch_client] = _override(None)
    try:
        client = TestClient(app)
        response = client.get("/api/v1/channel/ghost")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()
