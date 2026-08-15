"""OpenAI embeddings client.

Mirrors the TwitchClient pattern (async httpx client, DI-friendly) rather
than pulling in the openai SDK, keeping the project on a single HTTP client
convention.
"""

from __future__ import annotations

import httpx

from app.core.config import settings

OPENAI_BASE = "https://api.openai.com/v1"
EMBEDDING_MODEL = "text-embedding-3-small"


class EmbeddingClient:
    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client or httpx.AsyncClient(base_url=OPENAI_BASE, timeout=30.0)

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts, preserving input order regardless of API response order."""
        if not texts:
            return []
        response = await self._client.post(
            "/embeddings",
            json={"model": EMBEDDING_MODEL, "input": texts},
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
        )
        response.raise_for_status()
        data = response.json()["data"]
        ordered = sorted(data, key=lambda item: item["index"])
        return [item["embedding"] for item in ordered]

    async def aclose(self) -> None:
        await self._client.aclose()


_client: EmbeddingClient | None = None


def get_embedding_client() -> EmbeddingClient:
    """FastAPI dependency: shared EmbeddingClient instance."""
    global _client
    if _client is None:
        _client = EmbeddingClient()
    return _client


__all__ = ["EmbeddingClient", "get_embedding_client", "OPENAI_BASE", "EMBEDDING_MODEL"]
