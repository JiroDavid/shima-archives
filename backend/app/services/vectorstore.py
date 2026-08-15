"""Chroma vector store wrapper for embedded chat chunks (local dev)."""

from __future__ import annotations

import chromadb
from chromadb.api import ClientAPI

from app.core.config import settings
from app.services.chunking import ChatChunk

COLLECTION_NAME = "chat_chunks"


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
                    "start_message_id": c.start_message_id,
                    "end_message_id": c.end_message_id,
                    "start_offset_secs": c.start_offset_secs,
                    "end_offset_secs": c.end_offset_secs,
                    "message_count": c.message_count,
                }
                for c in chunks
            ],
        )


_store: ChromaStore | None = None


def get_chroma_store() -> ChromaStore:
    """FastAPI dependency: shared ChromaStore instance."""
    global _store
    if _store is None:
        _store = ChromaStore()
    return _store


__all__ = ["ChromaStore", "get_chroma_store", "COLLECTION_NAME"]
