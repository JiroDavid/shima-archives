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


class TwitchVod(BaseModel):
    """A channel's VOD resolved live from the Twitch Helix /videos endpoint."""

    twitch_vod_id: str
    user_id: str
    title: str
    description: str = ""
    url: str
    thumbnail_url: str = ""
    created_at: datetime | None = None
    published_at: datetime | None = None
    duration: str
    view_count: int = 0
    type: str = "archive"
    viewable: str = "public"
