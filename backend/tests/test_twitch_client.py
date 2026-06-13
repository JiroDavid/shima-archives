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
