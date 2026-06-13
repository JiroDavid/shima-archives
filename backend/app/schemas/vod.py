from datetime import datetime

from pydantic import BaseModel, ConfigDict


class VodRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    twitch_vod_id: str
    channel_id: int
    title: str | None = None
    duration_seconds: int | None = None
    stream_date: datetime | None = None
    published: bool | None = None
    thumbnail_url: str | None = None
    chat_ingested: bool
