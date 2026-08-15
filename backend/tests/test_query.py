from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.channel import Channel
from app.services.embeddings import get_embedding_client
from app.services.llm import get_gemini_client
from app.services.vectorstore import ChunkMatch, get_chroma_store


class FakeEmbeddingClient:
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2] for _ in texts]


class FakeChromaStore:
    def __init__(self, matches: list[ChunkMatch]) -> None:
        self._matches = matches
        self.query_calls: list[dict[str, Any]] = []

    def query_chunks(
        self,
        embedding: list[float],
        *,
        top_k: int = 8,
        channel_id: int | None = None,
        twitch_vod_id: str | None = None,
    ) -> list[ChunkMatch]:
        self.query_calls.append(
            {"top_k": top_k, "channel_id": channel_id, "twitch_vod_id": twitch_vod_id}
        )
        return self._matches


class FakeGeminiClient:
    def __init__(self, answer: str = "chat went crazy at 12:03") -> None:
        self.answer = answer
        self.prompts: list[str] = []

    async def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.answer


SAMPLE_MATCH = ChunkMatch(
    text="Bob: LUL chat went crazy\nAlice: fr fr",
    twitch_vod_id="987654",
    start_message_id=1,
    start_offset_secs=723,
    end_offset_secs=770,
)


def _override(embedder: Any, store: Any, llm: Any) -> None:
    app.dependency_overrides[get_embedding_client] = lambda: embedder
    app.dependency_overrides[get_chroma_store] = lambda: store
    app.dependency_overrides[get_gemini_client] = lambda: llm


def _clear() -> None:
    app.dependency_overrides.pop(get_embedding_client, None)
    app.dependency_overrides.pop(get_chroma_store, None)
    app.dependency_overrides.pop(get_gemini_client, None)


def test_query_returns_answer_and_sources(client: TestClient) -> None:
    llm = FakeGeminiClient()
    _override(FakeEmbeddingClient(), FakeChromaStore([SAMPLE_MATCH]), llm)
    try:
        response = client.post("/api/v1/query", json={"question": "when did chat go crazy?"})
        assert response.status_code == 200
        body = response.json()
        assert body["answer"] == "chat went crazy at 12:03"
        assert body["sources"] == [
            {
                "vod_id": "987654",
                "vod_offset_secs": 723,
                "message_preview": "Bob: LUL chat went crazy\nAlice: fr fr",
            }
        ]
        assert "when did chat go crazy?" in llm.prompts[0]
    finally:
        _clear()


def test_query_returns_no_data_message_when_no_matches(client: TestClient) -> None:
    llm = FakeGeminiClient()
    _override(FakeEmbeddingClient(), FakeChromaStore([]), llm)
    try:
        response = client.post("/api/v1/query", json={"question": "anything?"})
        assert response.status_code == 200
        body = response.json()
        assert body["sources"] == []
        assert llm.prompts == []  # no LLM call when there's nothing to answer from
    finally:
        _clear()


async def test_query_scoped_to_known_channel_resolves_channel_id(
    client: TestClient, db_session: AsyncSession
) -> None:
    channel = Channel(twitch_id="12345", username="yugi2x", display_name="Yugi2x")
    db_session.add(channel)
    await db_session.commit()

    store = FakeChromaStore([SAMPLE_MATCH])
    _override(FakeEmbeddingClient(), store, FakeGeminiClient())
    try:
        response = client.post(
            "/api/v1/query", json={"question": "hi", "channel": "yugi2x"}
        )
        assert response.status_code == 200
    finally:
        _clear()

    assert store.query_calls[0]["channel_id"] == channel.id


def test_query_scoped_to_unknown_channel_skips_search(client: TestClient) -> None:
    store = FakeChromaStore([SAMPLE_MATCH])
    llm = FakeGeminiClient()
    _override(FakeEmbeddingClient(), store, llm)
    try:
        response = client.post(
            "/api/v1/query", json={"question": "hi", "channel": "ghost"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["sources"] == []
    finally:
        _clear()
    assert store.query_calls == []
    assert llm.prompts == []


def test_query_passes_vod_id_and_top_k_through(client: TestClient) -> None:
    store = FakeChromaStore([SAMPLE_MATCH])
    _override(FakeEmbeddingClient(), store, FakeGeminiClient())
    try:
        response = client.post(
            "/api/v1/query",
            json={"question": "hi", "vod_id": "987654", "top_k": 3},
        )
        assert response.status_code == 200
    finally:
        _clear()

    assert store.query_calls[0]["twitch_vod_id"] == "987654"
    assert store.query_calls[0]["top_k"] == 3
