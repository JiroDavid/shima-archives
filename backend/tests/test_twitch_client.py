from typing import Any

import httpx

from app.services.twitch import HELIX_BASE, TwitchClient

SAMPLE_USER = {
    "id": "12345",
    "login": "yugi2x",
    "display_name": "Yugi2x",
    "broadcaster_type": "partner",
    "description": "card games",
    "profile_image_url": "https://example.com/yugi.png",
    "created_at": "2018-01-01T00:00:00Z",
}


def _make_video(vod_id: str) -> dict[str, Any]:
    return {
        "id": vod_id,
        "user_id": "12345",
        "user_login": "yugi2x",
        "user_name": "Yugi2x",
        "title": f"stream {vod_id}",
        "description": "",
        "created_at": "2024-01-01T00:00:00Z",
        "published_at": "2024-01-01T03:00:00Z",
        "url": f"https://twitch.tv/videos/{vod_id}",
        "thumbnail_url": "https://example.com/thumb.png",
        "viewable": "public",
        "view_count": 100,
        "language": "en",
        "type": "archive",
        "duration": "3h8m33s",
    }


def _make_client(users: list[dict[str, Any]]) -> TwitchClient:
    def handler(request: httpx.Request) -> httpx.Response:
        if "oauth2/token" in str(request.url):
            return httpx.Response(
                200, json={"access_token": "app-token", "expires_in": 3600}
            )
        if request.url.path.endswith("/users"):
            return httpx.Response(200, json={"data": users})
        return httpx.Response(404, json={})

    transport = httpx.MockTransport(handler)
    http = httpx.AsyncClient(transport=transport, base_url=HELIX_BASE)
    return TwitchClient(client=http)


async def test_get_user_returns_user_when_present() -> None:
    client = _make_client([SAMPLE_USER])
    user = await client.get_user("yugi2x")
    assert user is not None
    assert user["id"] == "12345"
    assert user["login"] == "yugi2x"
    await client.aclose()


async def test_get_user_returns_none_when_absent() -> None:
    client = _make_client([])
    user = await client.get_user("ghost")
    assert user is None
    await client.aclose()


async def test_get_videos_returns_archives() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "oauth2/token" in str(request.url):
            return httpx.Response(
                200, json={"access_token": "app-token", "expires_in": 3600}
            )
        return httpx.Response(
            200,
            json={"data": [_make_video("v1"), _make_video("v2")], "pagination": {}},
        )

    transport = httpx.MockTransport(handler)
    http = httpx.AsyncClient(transport=transport, base_url=HELIX_BASE)
    client = TwitchClient(client=http)

    videos = await client.get_videos("12345")

    assert [v["id"] for v in videos] == ["v1", "v2"]
    await client.aclose()


async def test_get_videos_paginates_until_cursor_empty() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "oauth2/token" in str(request.url):
            return httpx.Response(
                200, json={"access_token": "app-token", "expires_in": 3600}
            )
        after = request.url.params.get("after")
        if after is None:
            return httpx.Response(
                200,
                json={"data": [_make_video("v1")], "pagination": {"cursor": "next"}},
            )
        return httpx.Response(
            200, json={"data": [_make_video("v2")], "pagination": {}}
        )

    transport = httpx.MockTransport(handler)
    http = httpx.AsyncClient(transport=transport, base_url=HELIX_BASE)
    client = TwitchClient(client=http)

    videos = await client.get_videos("12345")

    assert [v["id"] for v in videos] == ["v1", "v2"]
    await client.aclose()


async def test_get_videos_sends_user_id_and_archive_type() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if "oauth2/token" in str(request.url):
            return httpx.Response(
                200, json={"access_token": "app-token", "expires_in": 3600}
            )
        captured["user_id"] = request.url.params.get("user_id", "")
        captured["type"] = request.url.params.get("type", "")
        captured["authorization"] = request.headers.get("Authorization", "")
        return httpx.Response(200, json={"data": [], "pagination": {}})

    transport = httpx.MockTransport(handler)
    http = httpx.AsyncClient(transport=transport, base_url=HELIX_BASE)
    client = TwitchClient(client=http)

    await client.get_videos("12345")

    assert captured["user_id"] == "12345"
    assert captured["type"] == "archive"
    assert captured["authorization"] == "Bearer app-token"
    await client.aclose()


async def test_get_user_sends_auth_and_client_id_headers() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if "oauth2/token" in str(request.url):
            return httpx.Response(
                200, json={"access_token": "app-token", "expires_in": 3600}
            )
        captured["authorization"] = request.headers.get("Authorization", "")
        captured["client_id"] = request.headers.get("Client-Id", "")
        captured["login"] = request.url.params.get("login", "")
        return httpx.Response(200, json={"data": [SAMPLE_USER]})

    transport = httpx.MockTransport(handler)
    http = httpx.AsyncClient(transport=transport, base_url=HELIX_BASE)
    client = TwitchClient(client=http)

    await client.get_user("yugi2x")

    assert captured["authorization"] == "Bearer app-token"
    assert captured["login"] == "yugi2x"
    await client.aclose()
