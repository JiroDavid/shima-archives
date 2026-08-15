from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.channel import Channel
from app.models.chat_message import ChatMessage
from app.models.vod import Vod
from app.services.embeddings import get_embedding_client
from app.services.twitch import get_twitch_client
from app.services.vectorstore import ChromaStore, get_chroma_store

SAMPLE_USER = {"id": "12345", "login": "yugi2x", "display_name": "Yugi2x"}


class FakeTwitchClient:
    def __init__(self, user: dict[str, Any] | None) -> None:
        self._user = user

    async def get_user(self, username: str) -> dict[str, Any] | None:
        return self._user


class FakeEmbeddingClient:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(texts)
        return [[0.1, 0.2] for _ in texts]


async def _make_vod_with_messages(
    db_session: AsyncSession, *, message_count: int, chat_ingested: bool = True
) -> tuple[Channel, Vod]:
    channel = Channel(twitch_id="12345", username="yugi2x", display_name="Yugi2x")
    db_session.add(channel)
    await db_session.flush()

    vod = Vod(
        twitch_vod_id="987654",
        channel_id=channel.id,
        chat_ingested=chat_ingested,
        chunks_ingested=False,
    )
    db_session.add(vod)
    await db_session.flush()

    db_session.add_all(
        [
            ChatMessage(
                channel_id=channel.id,
                vod_id=vod.id,
                username=f"user{i}",
                message=f"message {i}",
                sent_at=datetime(2024, 1, 1, tzinfo=UTC),
                vod_offset_secs=i,
                source="vod_replay",
            )
            for i in range(message_count)
        ]
    )
    await db_session.commit()
    return channel, vod


def _override_deps(
    twitch: FakeTwitchClient, embedder: FakeEmbeddingClient, store: ChromaStore
) -> None:
    app.dependency_overrides[get_twitch_client] = lambda: twitch
    app.dependency_overrides[get_embedding_client] = lambda: embedder
    app.dependency_overrides[get_chroma_store] = lambda: store


def _clear_overrides() -> None:
    app.dependency_overrides.pop(get_twitch_client, None)
    app.dependency_overrides.pop(get_embedding_client, None)
    app.dependency_overrides.pop(get_chroma_store, None)


def test_ingest_returns_404_when_channel_unknown_to_twitch(
    client: TestClient, tmp_path: Path
) -> None:
    _override_deps(FakeTwitchClient(None), FakeEmbeddingClient(), ChromaStore.__new__(ChromaStore))
    try:
        response = client.post("/api/v1/ingest/ghost")
        assert response.status_code == 404
    finally:
        _clear_overrides()


def test_ingest_is_a_noop_when_channel_not_yet_persisted_locally(
    client: TestClient, tmp_path: Path
) -> None:
    import chromadb

    store = ChromaStore(client=chromadb.PersistentClient(path=str(tmp_path)))
    _override_deps(FakeTwitchClient(SAMPLE_USER), FakeEmbeddingClient(), store)
    try:
        response = client.post("/api/v1/ingest/yugi2x")
        assert response.status_code == 200
        body = response.json()
        assert body == {"channel": "yugi2x", "vods_processed": 0, "chunks_created": 0}
    finally:
        _clear_overrides()


async def test_ingest_chunks_and_embeds_persisted_vod_chat(
    client: TestClient, db_session: AsyncSession, tmp_path: Path
) -> None:
    import chromadb

    channel, vod = await _make_vod_with_messages(db_session, message_count=60)

    store = ChromaStore(client=chromadb.PersistentClient(path=str(tmp_path)))
    embedder = FakeEmbeddingClient()
    _override_deps(FakeTwitchClient(SAMPLE_USER), embedder, store)
    try:
        response = client.post("/api/v1/ingest/yugi2x")
        assert response.status_code == 200
        body = response.json()
        assert body["channel"] == "yugi2x"
        assert body["vods_processed"] == 1
        assert body["chunks_created"] == 2  # 60 messages, window=50/overlap=10 -> 2 chunks
    finally:
        _clear_overrides()

    assert len(embedder.calls) == 1
    assert len(embedder.calls[0]) == 2

    await db_session.refresh(vod)
    assert vod.chunks_ingested is True


async def test_ingest_skips_vods_without_persisted_chat(
    client: TestClient, db_session: AsyncSession, tmp_path: Path
) -> None:
    import chromadb

    await _make_vod_with_messages(db_session, message_count=60, chat_ingested=False)

    store = ChromaStore(client=chromadb.PersistentClient(path=str(tmp_path)))
    embedder = FakeEmbeddingClient()
    _override_deps(FakeTwitchClient(SAMPLE_USER), embedder, store)
    try:
        response = client.post("/api/v1/ingest/yugi2x")
        assert response.status_code == 200
        body = response.json()
        assert body["vods_processed"] == 0
        assert body["chunks_created"] == 0
    finally:
        _clear_overrides()
    assert embedder.calls == []


async def test_ingest_skips_vods_already_chunk_ingested(
    client: TestClient, db_session: AsyncSession, tmp_path: Path
) -> None:
    import chromadb

    channel, vod = await _make_vod_with_messages(db_session, message_count=60)
    vod.chunks_ingested = True
    await db_session.commit()

    store = ChromaStore(client=chromadb.PersistentClient(path=str(tmp_path)))
    embedder = FakeEmbeddingClient()
    _override_deps(FakeTwitchClient(SAMPLE_USER), embedder, store)
    try:
        response = client.post("/api/v1/ingest/yugi2x")
        assert response.status_code == 200
        body = response.json()
        assert body["vods_processed"] == 0
        assert body["chunks_created"] == 0
    finally:
        _clear_overrides()
    assert embedder.calls == []
