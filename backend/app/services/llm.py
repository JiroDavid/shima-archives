"""Gemini Flash client (Google AI Studio) for RAG answer generation.

Mirrors the TwitchClient / EmbeddingClient pattern (async httpx client,
DI-friendly) instead of pulling in a Google SDK.
"""

from __future__ import annotations

import httpx

from app.core.config import settings

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"


class GeminiClient:
    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client or httpx.AsyncClient(base_url=GEMINI_BASE, timeout=30.0)

    async def generate(self, prompt: str) -> str:
        response = await self._client.post(
            f"/models/{settings.gemini_model}:generateContent",
            params={"key": settings.gemini_api_key},
            json={"contents": [{"parts": [{"text": prompt}]}]},
        )
        response.raise_for_status()
        payload = response.json()
        text: str = payload["candidates"][0]["content"]["parts"][0]["text"]
        return text

    async def aclose(self) -> None:
        await self._client.aclose()


_client: GeminiClient | None = None


def get_gemini_client() -> GeminiClient:
    """FastAPI dependency: shared GeminiClient instance."""
    global _client
    if _client is None:
        _client = GeminiClient()
    return _client


__all__ = ["GeminiClient", "get_gemini_client", "GEMINI_BASE"]
