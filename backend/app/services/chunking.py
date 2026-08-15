"""Chat message chunking for embedding.

Chunks are fixed-size, overlapping windows over an already-ordered sequence
of messages (per CLAUDE.md: 50-message windows, 10-message overlap), so
adjacent chunks share context and a query landing near a window boundary
still has surrounding messages to match against.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.models.chat_message import ChatMessage

DEFAULT_WINDOW = 50
DEFAULT_OVERLAP = 10


@dataclass
class ChatChunk:
    channel_id: int
    vod_id: int
    twitch_vod_id: str
    text: str
    start_message_id: int
    end_message_id: int
    start_offset_secs: int
    end_offset_secs: int
    start_sent_at: datetime
    end_sent_at: datetime
    message_count: int


def chunk_messages(
    messages: list[ChatMessage],
    *,
    vod_id: int,
    channel_id: int,
    twitch_vod_id: str,
    window: int = DEFAULT_WINDOW,
    overlap: int = DEFAULT_OVERLAP,
) -> list[ChatChunk]:
    """Chunk an already-ordered list of messages into overlapping windows."""
    if not messages:
        return []

    stride = window - overlap
    chunks: list[ChatChunk] = []
    start = 0
    while True:
        batch = messages[start : start + window]
        chunks.append(
            ChatChunk(
                channel_id=channel_id,
                vod_id=vod_id,
                twitch_vod_id=twitch_vod_id,
                text="\n".join(f"{m.username}: {m.message}" for m in batch),
                start_message_id=batch[0].id,
                end_message_id=batch[-1].id,
                start_offset_secs=batch[0].vod_offset_secs or 0,
                end_offset_secs=batch[-1].vod_offset_secs or 0,
                start_sent_at=batch[0].sent_at,
                end_sent_at=batch[-1].sent_at,
                message_count=len(batch),
            )
        )
        if start + window >= len(messages):
            break
        start += stride
    return chunks
