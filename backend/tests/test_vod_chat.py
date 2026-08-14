from collections.abc import Callable
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.channel import Channel
from app.models.chat_message import ChatMessage
from app.models.vod import Vod
from app.services.twitch import get_twitch_client

SAMPLE_COMMENT = {
    "_id": "abc",
    "created_at": "2024-01-01T00:00:12Z",
    "content_offset_seconds": 12.5,
    "commenter": {"display_name": "Bob", "name": "bob"},
    "message": {"body": "LUL chat went crazy", "user_color": "#FF0000"},
}

SAMPLE_VIDEO = {
    "id": "987654",
    "user_id": "12345",
    "user_login": "yugi2x",
    "user_name": "Yugi2x",
    "title": "ranked grind",
    "thumbnail_url": "https://example.com/thumb.png",
}


class FakeTwitchClient:
    def __init__(
        self, comments: list[dict[str, Any]], video: dict[str, Any] | None = SAMPLE_VIDEO
    ) -> None:
        self._comments = comments
        self._video = video
        self.get_vod_comments_calls = 0

    async def get_vod_comments(self, vod_id: str) -> list[dict[str, Any]]:
        self.get_vod_comments_calls += 1
        return self._comments

    async def get_video(self, vod_id: str) -> dict[str, Any] | None:
        return self._video


def _override(fake: FakeTwitchClient) -> Callable[[], FakeTwitchClient]:
    def factory() -> FakeTwitchClient:
        return fake

    return factory


def test_get_vod_chat_returns_comments(client: TestClient) -> None:
    fake = FakeTwitchClient([SAMPLE_COMMENT])
    app.dependency_overrides[get_twitch_client] = _override(fake)
    try:
        response = client.get("/api/v1/vod/987654/chat")
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["username"] == "Bob"
        assert body[0]["message"] == "LUL chat went crazy"
        assert body[0]["offset_seconds"] == 12.5
        assert body[0]["color"] == "#FF0000"
    finally:
        app.dependency_overrides.pop(get_twitch_client, None)


def test_get_vod_chat_returns_empty_list_when_none(client: TestClient) -> None:
    fake = FakeTwitchClient([])
    app.dependency_overrides[get_twitch_client] = _override(fake)
    try:
        response = client.get("/api/v1/vod/987654/chat")
        assert response.status_code == 200
        assert response.json() == []
    finally:
        app.dependency_overrides.pop(get_twitch_client, None)


async def test_get_vod_chat_persists_channel_vod_and_messages(
    client: TestClient, db_session: AsyncSession
) -> None:
    fake = FakeTwitchClient([SAMPLE_COMMENT])
    app.dependency_overrides[get_twitch_client] = _override(fake)
    try:
        response = client.get("/api/v1/vod/987654/chat")
        assert response.status_code == 200
    finally:
        app.dependency_overrides.pop(get_twitch_client, None)

    channel = await db_session.scalar(select(Channel).where(Channel.twitch_id == "12345"))
    assert channel is not None
    assert channel.username == "yugi2x"

    vod = await db_session.scalar(select(Vod).where(Vod.twitch_vod_id == "987654"))
    assert vod is not None
    assert vod.chat_ingested is True
    assert vod.channel_id == channel.id

    messages = (
        await db_session.scalars(select(ChatMessage).where(ChatMessage.vod_id == vod.id))
    ).all()
    assert len(messages) == 1
    assert messages[0].source == "vod_replay"
    assert messages[0].username == "Bob"


def test_get_vod_chat_serves_from_db_on_second_request_without_hitting_twitch(
    client: TestClient,
) -> None:
    fake = FakeTwitchClient([SAMPLE_COMMENT])
    app.dependency_overrides[get_twitch_client] = _override(fake)
    try:
        first = client.get("/api/v1/vod/987654/chat")
        assert first.status_code == 200
        assert fake.get_vod_comments_calls == 1

        second = client.get("/api/v1/vod/987654/chat")
        assert second.status_code == 200
        assert fake.get_vod_comments_calls == 1  # not called again

        body = second.json()
        assert len(body) == 1
        assert body[0]["username"] == "Bob"
        assert body[0]["message"] == "LUL chat went crazy"
    finally:
        app.dependency_overrides.pop(get_twitch_client, None)


def test_get_vod_chat_returns_404_when_vod_unknown_to_twitch(client: TestClient) -> None:
    fake = FakeTwitchClient([SAMPLE_COMMENT], video=None)
    app.dependency_overrides[get_twitch_client] = _override(fake)
    try:
        response = client.get("/api/v1/vod/000000/chat")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.pop(get_twitch_client, None)
