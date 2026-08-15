from typing import Any

import httpx

from app.services.llm import GEMINI_BASE, GeminiClient


def _make_client(handler: Any) -> GeminiClient:
    transport = httpx.MockTransport(handler)
    http = httpx.AsyncClient(transport=transport, base_url=GEMINI_BASE)
    return GeminiClient(client=http)


async def test_generate_returns_text_from_first_candidate() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {"content": {"parts": [{"text": "Skullmanjackk said it around 1am."}]}}
                ]
            },
        )

    client = _make_client(handler)
    answer = await client.generate("when did Skullmanjackk mention shiesty?")
    assert answer == "Skullmanjackk said it around 1am."
    await client.aclose()


async def test_generate_sends_prompt_and_api_key() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        import json

        captured["body"] = json.loads(request.read())
        captured["has_key_header"] = "x-goog-api-key" in request.headers
        captured["key_in_url"] = "key=" in str(request.url)
        captured["path"] = request.url.path
        return httpx.Response(
            200, json={"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}
        )

    client = _make_client(handler)
    await client.generate("hello")

    assert captured["body"]["contents"][0]["parts"][0]["text"] == "hello"
    assert captured["has_key_header"] is True
    assert captured["key_in_url"] is False
    assert captured["path"].endswith(":generateContent")
    await client.aclose()
