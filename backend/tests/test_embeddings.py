from typing import Any

import httpx

from app.services.embeddings import OPENAI_BASE, EmbeddingClient


def _make_client(handler: Any) -> EmbeddingClient:
    transport = httpx.MockTransport(handler)
    http = httpx.AsyncClient(transport=transport, base_url=OPENAI_BASE)
    return EmbeddingClient(client=http)


async def test_embed_texts_returns_empty_list_for_empty_input() -> None:
    client = _make_client(lambda request: httpx.Response(500))
    result = await client.embed_texts([])
    assert result == []
    await client.aclose()


async def test_embed_texts_returns_vectors_in_input_order() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "data": [
                    {"index": 1, "embedding": [0.4, 0.5]},
                    {"index": 0, "embedding": [0.1, 0.2]},
                ]
            },
        )

    client = _make_client(handler)
    vectors = await client.embed_texts(["first", "second"])
    assert vectors == [[0.1, 0.2], [0.4, 0.5]]
    await client.aclose()


async def test_embed_texts_sends_model_input_and_auth_header() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = request.read()
        captured["authorization"] = request.headers.get("Authorization", "")
        return httpx.Response(200, json={"data": [{"index": 0, "embedding": [0.1]}]})

    client = _make_client(handler)
    await client.embed_texts(["hello"])

    import json

    body = json.loads(captured["body"])
    assert body["model"] == "text-embedding-3-small"
    assert body["input"] == ["hello"]
    assert captured["authorization"].startswith("Bearer ")
    await client.aclose()
