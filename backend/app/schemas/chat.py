from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ChatMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    channel_id: int
    vod_id: int | None = None
    username: str
    message: str
    sent_at: datetime
    vod_offset_secs: int | None = None
    badges: dict[str, Any] | None = None
    emote_ids: dict[str, Any] | None = None
    source: str
