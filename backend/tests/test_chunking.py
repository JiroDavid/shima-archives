from datetime import UTC, datetime, timedelta

from app.models.chat_message import ChatMessage
from app.services.chunking import chunk_messages


def _messages(count: int) -> list[ChatMessage]:
    base = datetime(2024, 1, 1, tzinfo=UTC)
    return [
        ChatMessage(
            id=i + 1,
            channel_id=1,
            vod_id=99,
            username=f"user{i}",
            message=f"message {i}",
            sent_at=base + timedelta(seconds=i),
            vod_offset_secs=i,
            source="vod_replay",
        )
        for i in range(count)
    ]


def test_empty_messages_produce_no_chunks() -> None:
    assert chunk_messages([], vod_id=99, channel_id=1) == []


def test_fewer_messages_than_window_produce_one_chunk() -> None:
    chunks = chunk_messages(_messages(10), vod_id=99, channel_id=1)
    assert len(chunks) == 1
    assert chunks[0].message_count == 10
    assert chunks[0].start_message_id == 1
    assert chunks[0].end_message_id == 10


def test_exactly_one_window_produces_one_chunk() -> None:
    chunks = chunk_messages(_messages(50), vod_id=99, channel_id=1)
    assert len(chunks) == 1
    assert chunks[0].message_count == 50


def test_windows_overlap_by_configured_amount() -> None:
    # stride = 50 - 10 = 40, so second window starts at message index 40
    chunks = chunk_messages(_messages(90), vod_id=99, channel_id=1)
    assert len(chunks) == 2
    assert chunks[0].start_message_id == 1
    assert chunks[0].end_message_id == 50
    assert chunks[1].start_message_id == 41
    assert chunks[1].end_message_id == 90


def test_custom_window_and_overlap() -> None:
    chunks = chunk_messages(_messages(15), vod_id=99, channel_id=1, window=10, overlap=5)
    assert len(chunks) == 2
    assert chunks[0].start_message_id == 1
    assert chunks[0].end_message_id == 10
    assert chunks[1].start_message_id == 6
    assert chunks[1].end_message_id == 15


def test_chunk_text_joins_username_and_message() -> None:
    chunks = chunk_messages(_messages(2), vod_id=99, channel_id=1)
    assert chunks[0].text == "user0: message 0\nuser1: message 1"


def test_chunk_carries_vod_and_channel_ids() -> None:
    chunks = chunk_messages(_messages(3), vod_id=42, channel_id=7)
    assert chunks[0].vod_id == 42
    assert chunks[0].channel_id == 7


def test_chunk_offsets_and_timestamps_span_the_window() -> None:
    chunks = chunk_messages(_messages(5), vod_id=99, channel_id=1)
    chunk = chunks[0]
    assert chunk.start_offset_secs == 0
    assert chunk.end_offset_secs == 4
    assert chunk.start_sent_at == datetime(2024, 1, 1, tzinfo=UTC)
    assert chunk.end_sent_at == datetime(2024, 1, 1, 0, 0, 4, tzinfo=UTC)
