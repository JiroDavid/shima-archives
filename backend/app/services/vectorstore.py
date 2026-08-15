"""Chroma vector store wrapper for embedded chat chunks (local dev)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import chromadb
from chromadb.api import ClientAPI

from app.core.config import settings
from app.services.chunking import ChatChunk

COLLECTION_NAME = "chat_chunks"


@dataclass
class ChunkMatch:
    text: str
    twitch_vod_id: str
    start_message_id: int
    start_offset_secs: int
    end_offset_secs: int


class ChromaStore:
    def __init__(self, client: ClientAPI | None = None) -> None:
        self._client = client or chromadb.PersistentClient(path=settings.chroma_path)
        self._collection = self._client.get_or_create_collection(COLLECTION_NAME)

    def upsert_chunks(self, chunks: list[ChatChunk], embeddings: list[list[float]]) -> None:
        """Upsert chunks by a stable vod+start-message id, so re-ingestion doesn't duplicate."""
        if not chunks:
            return
        self._collection.upsert(
            ids=[f"vod-{c.vod_id}-{c.start_message_id}" for c in chunks],
            embeddings=embeddings,  # type: ignore[arg-type]
            documents=[c.text for c in chunks],
            metadatas=[
                {
                    "channel_id": c.channel_id,
                    "vod_id": c.vod_id,
                    "twitch_vod_id": c.twitch_vod_id,
                    "start_message_id": c.start_message_id,
                    "end_message_id": c.end_message_id,
                    "start_offset_secs": c.start_offset_secs,
                    "end_offset_secs": c.end_offset_secs,
                    "message_count": c.message_count,
                }
                for c in chunks
            ],
        )

    def query_chunks(
        self,
        embedding: list[float],
        *,
        top_k: int = 8,
        channel_id: int | None = None,
        twitch_vod_id: str | None = None,
    ) -> list[ChunkMatch]:
        """Nearest-neighbor search, optionally scoped to a channel and/or VOD."""
        if self._collection.count() == 0:
            return []

        conditions: list[dict[str, Any]] = []
        if channel_id is not None:
            conditions.append({"channel_id": channel_id})
        if twitch_vod_id is not None:
            conditions.append({"twitch_vod_id": twitch_vod_id})
        where: dict[str, Any] | None
        if len(conditions) > 1:
            where = {"$and": conditions}
        elif conditions:
            where = conditions[0]
        else:
            where = None

        result = self._collection.query(
            query_embeddings=[embedding],  # type: ignore[arg-type]
            n_results=top_k,
            where=where,
            include=["documents", "metadatas"],
        )
        documents = result["documents"][0] if result["documents"] else []
        metadatas = result["metadatas"][0] if result["metadatas"] else []
        return [
            ChunkMatch(
                text=str(doc),
                twitch_vod_id=str(meta["twitch_vod_id"]),
                start_message_id=int(meta["start_message_id"]),  # type: ignore[arg-type]
                start_offset_secs=int(meta["start_offset_secs"]),  # type: ignore[arg-type]
                end_offset_secs=int(meta["end_offset_secs"]),  # type: ignore[arg-type]
            )
            for doc, meta in zip(documents, metadatas, strict=True)
        ]


_store: ChromaStore | None = None


def get_chroma_store() -> ChromaStore:
    """FastAPI dependency: shared ChromaStore instance."""
    global _store
    if _store is None:
        _store = ChromaStore()
    return _store


__all__ = ["ChromaStore", "get_chroma_store", "COLLECTION_NAME"]
