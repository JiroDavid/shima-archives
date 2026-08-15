from datetime import UTC, datetime
from pathlib import Path

import chromadb

from app.services.chunking import ChatChunk
from app.services.vectorstore import COLLECTION_NAME, ChromaStore


def _store(tmp_path: Path) -> ChromaStore:
    client = chromadb.PersistentClient(path=str(tmp_path))
    return ChromaStore(client=client)


def _chunk(
    start_id: int, vod_id: int = 99, channel_id: int = 1, twitch_vod_id: str = "987654"
) -> ChatChunk:
    return ChatChunk(
        channel_id=channel_id,
        vod_id=vod_id,
        twitch_vod_id=twitch_vod_id,
        text=f"chunk starting at {start_id}",
        start_message_id=start_id,
        end_message_id=start_id + 49,
        start_offset_secs=start_id,
        end_offset_secs=start_id + 49,
        start_sent_at=datetime(2024, 1, 1, tzinfo=UTC),
        end_sent_at=datetime(2024, 1, 1, tzinfo=UTC),
        message_count=50,
    )


def test_upsert_chunks_with_no_chunks_is_a_noop(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.upsert_chunks([], [])  # should not raise


def test_upsert_chunks_stores_documents_and_metadata(tmp_path: Path) -> None:
    store = _store(tmp_path)
    chunks = [_chunk(1), _chunk(41)]
    embeddings = [[0.1, 0.2], [0.3, 0.4]]

    store.upsert_chunks(chunks, embeddings)

    client = chromadb.PersistentClient(path=str(tmp_path))
    collection = client.get_collection(COLLECTION_NAME)
    assert collection.count() == 2

    result = collection.get(ids=["vod-99-1"], include=["documents", "metadatas"])
    assert result["documents"][0] == "chunk starting at 1"
    assert result["metadatas"][0]["vod_id"] == 99
    assert result["metadatas"][0]["channel_id"] == 1
    assert result["metadatas"][0]["start_offset_secs"] == 1
    assert result["metadatas"][0]["message_count"] == 50


def test_upsert_chunks_is_idempotent_on_rerun(tmp_path: Path) -> None:
    store = _store(tmp_path)
    chunk = _chunk(1)

    store.upsert_chunks([chunk], [[0.1, 0.2]])
    store.upsert_chunks([chunk], [[0.1, 0.2]])

    client = chromadb.PersistentClient(path=str(tmp_path))
    collection = client.get_collection(COLLECTION_NAME)
    assert collection.count() == 1


def test_query_chunks_returns_empty_list_when_collection_empty(tmp_path: Path) -> None:
    store = _store(tmp_path)
    assert store.query_chunks([0.1, 0.2]) == []


def test_query_chunks_orders_by_similarity(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.upsert_chunks(
        [_chunk(1), _chunk(41)],
        [[1.0, 0.0], [0.0, 1.0]],
    )

    matches = store.query_chunks([0.9, 0.1])

    assert [m.start_message_id for m in matches] == [1, 41]
    assert matches[0].text == "chunk starting at 1"
    assert matches[0].twitch_vod_id == "987654"
    assert matches[0].start_offset_secs == 1


def test_query_chunks_respects_top_k(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.upsert_chunks(
        [_chunk(1), _chunk(41), _chunk(81)],
        [[1.0, 0.0], [0.9, 0.1], [0.0, 1.0]],
    )

    matches = store.query_chunks([1.0, 0.0], top_k=2)

    assert len(matches) == 2


def test_query_chunks_filters_by_channel_id(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.upsert_chunks(
        [_chunk(1, channel_id=1), _chunk(41, channel_id=2)],
        [[1.0, 0.0], [1.0, 0.0]],
    )

    matches = store.query_chunks([1.0, 0.0], channel_id=2)

    assert len(matches) == 1
    assert matches[0].start_message_id == 41


def test_query_chunks_filters_by_twitch_vod_id(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.upsert_chunks(
        [
            _chunk(1, twitch_vod_id="111"),
            _chunk(41, twitch_vod_id="222"),
        ],
        [[1.0, 0.0], [1.0, 0.0]],
    )

    matches = store.query_chunks([1.0, 0.0], twitch_vod_id="222")

    assert len(matches) == 1
    assert matches[0].twitch_vod_id == "222"
