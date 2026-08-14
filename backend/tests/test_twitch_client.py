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


async def test_get_video_returns_video_when_present() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "oauth2/token" in str(request.url):
            return httpx.Response(
                200, json={"access_token": "app-token", "expires_in": 3600}
            )
        assert request.url.params.get("id") == "987654"
        return httpx.Response(200, json={"data": [_make_video("987654")]})

    transport = httpx.MockTransport(handler)
    http = httpx.AsyncClient(transport=transport, base_url=HELIX_BASE)
    client = TwitchClient(client=http)

    video = await client.get_video("987654")

    assert video is not None
    assert video["id"] == "987654"
    assert video["user_id"] == "12345"
    await client.aclose()


async def test_get_video_returns_none_when_absent() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "oauth2/token" in str(request.url):
            return httpx.Response(
                200, json={"access_token": "app-token", "expires_in": 3600}
            )
        return httpx.Response(200, json={"data": []})

    transport = httpx.MockTransport(handler)
    http = httpx.AsyncClient(transport=transport, base_url=HELIX_BASE)
    client = TwitchClient(client=http)

    video = await client.get_video("ghost")

    assert video is None
    await client.aclose()


def _make_comment(offset: float) -> dict[str, Any]:
    return {
        "_id": f"c{offset}",
        "created_at": "2024-01-01T00:00:00Z",
        "content_offset_seconds": offset,
        "commenter": {"display_name": "Bob", "name": "bob"},
        "message": {"body": f"msg {offset}", "user_color": "#FF0000"},
    }


async def test_get_vod_comments_returns_comments() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "oauth2/token" in str(request.url):
            return httpx.Response(
                200, json={"access_token": "app-token", "expires_in": 3600}
            )
        return httpx.Response(
            200, json={"comments": [_make_comment(1.0), _make_comment(2.0)]}
        )

    transport = httpx.MockTransport(handler)
    http = httpx.AsyncClient(transport=transport, base_url=HELIX_BASE)
    client = TwitchClient(client=http)

    comments = await client.get_vod_comments("987654")

    assert [c["content_offset_seconds"] for c in comments] == [1.0, 2.0]
    await client.aclose()


async def test_get_vod_comments_paginates_until_next_empty() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "oauth2/token" in str(request.url):
            return httpx.Response(
                200, json={"access_token": "app-token", "expires_in": 3600}
            )
        cursor = request.url.params.get("cursor")
        if cursor is None:
            return httpx.Response(
                200, json={"comments": [_make_comment(1.0)], "_next": "page2"}
            )
        return httpx.Response(200, json={"comments": [_make_comment(2.0)]})

    transport = httpx.MockTransport(handler)
    http = httpx.AsyncClient(transport=transport, base_url=HELIX_BASE)
    client = TwitchClient(client=http)

    comments = await client.get_vod_comments("987654")

    assert [c["content_offset_seconds"] for c in comments] == [1.0, 2.0]
    await client.aclose()


async def test_get_vod_comments_requests_correct_path_and_auth() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if "oauth2/token" in str(request.url):
            return httpx.Response(
                200, json={"access_token": "app-token", "expires_in": 3600}
            )
        captured["path"] = request.url.path
        captured["authorization"] = request.headers.get("Authorization", "")
        captured["client_id"] = request.headers.get("Client-Id", "")
        return httpx.Response(200, json={"comments": []})

    transport = httpx.MockTransport(handler)
    http = httpx.AsyncClient(transport=transport, base_url=HELIX_BASE)
    client = TwitchClient(client=http)

    await client.get_vod_comments("987654")

    assert captured["path"] == "/helix/videos/987654/comments"
    assert captured["authorization"] == "Bearer app-token"
    await client.aclose()


def _make_clip(clip_id: str) -> dict[str, Any]:
    return {
        "id": clip_id,
        "url": f"https://clips.twitch.tv/{clip_id}",
        "broadcaster_id": "12345",
        "creator_id": "999",
        "creator_name": "Bob",
        "video_id": "987654",
        "game_id": "509658",
        "title": f"clip {clip_id}",
        "view_count": 42,
        "created_at": "2024-01-01T00:00:00Z",
        "thumbnail_url": "https://example.com/clip-thumb.png",
        "duration": 30.0,
    }


async def test_get_clips_returns_clips() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "oauth2/token" in str(request.url):
            return httpx.Response(
                200, json={"access_token": "app-token", "expires_in": 3600}
            )
        return httpx.Response(
            200,
            json={"data": [_make_clip("c1"), _make_clip("c2")], "pagination": {}},
        )

    transport = httpx.MockTransport(handler)
    http = httpx.AsyncClient(transport=transport, base_url=HELIX_BASE)
    client = TwitchClient(client=http)

    clips = await client.get_clips("12345")

    assert [c["id"] for c in clips] == ["c1", "c2"]
    await client.aclose()


async def test_get_clips_paginates_until_cursor_empty() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "oauth2/token" in str(request.url):
            return httpx.Response(
                200, json={"access_token": "app-token", "expires_in": 3600}
            )
        after = request.url.params.get("after")
        if after is None:
            return httpx.Response(
                200,
                json={"data": [_make_clip("c1")], "pagination": {"cursor": "next"}},
            )
        return httpx.Response(200, json={"data": [_make_clip("c2")], "pagination": {}})

    transport = httpx.MockTransport(handler)
    http = httpx.AsyncClient(transport=transport, base_url=HELIX_BASE)
    client = TwitchClient(client=http)

    clips = await client.get_clips("12345")

    assert [c["id"] for c in clips] == ["c1", "c2"]
    await client.aclose()


async def test_get_clips_sends_broadcaster_id_and_optional_filters() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if "oauth2/token" in str(request.url):
            return httpx.Response(
                200, json={"access_token": "app-token", "expires_in": 3600}
            )
        captured["broadcaster_id"] = request.url.params.get("broadcaster_id", "")
        captured["game_id"] = request.url.params.get("game_id", "")
        captured["started_at"] = request.url.params.get("started_at", "")
        captured["ended_at"] = request.url.params.get("ended_at", "")
        captured["authorization"] = request.headers.get("Authorization", "")
        return httpx.Response(200, json={"data": [], "pagination": {}})

    transport = httpx.MockTransport(handler)
    http = httpx.AsyncClient(transport=transport, base_url=HELIX_BASE)
    client = TwitchClient(client=http)

    await client.get_clips(
        "12345",
        game_id="509658",
        started_at="2024-01-01T00:00:00Z",
        ended_at="2024-02-01T00:00:00Z",
    )

    assert captured["broadcaster_id"] == "12345"
    assert captured["game_id"] == "509658"
    assert captured["started_at"] == "2024-01-01T00:00:00Z"
    assert captured["ended_at"] == "2024-02-01T00:00:00Z"
    assert captured["authorization"] == "Bearer app-token"
    await client.aclose()


async def test_get_clips_omits_absent_filters() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if "oauth2/token" in str(request.url):
            return httpx.Response(
                200, json={"access_token": "app-token", "expires_in": 3600}
            )
        captured["params"] = ",".join(sorted(request.url.params.keys()))
        return httpx.Response(200, json={"data": [], "pagination": {}})

    transport = httpx.MockTransport(handler)
    http = httpx.AsyncClient(transport=transport, base_url=HELIX_BASE)
    client = TwitchClient(client=http)

    await client.get_clips("12345")

    assert captured["params"] == "broadcaster_id,first"
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
