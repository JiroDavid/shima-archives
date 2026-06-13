from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChannelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    twitch_id: str
    username: str
    display_name: str | None = None
    indexed_at: datetime | None = None
    bot_active: bool


class TwitchChannel(BaseModel):
    """Public channel info resolved live from the Twitch Helix /users endpoint."""

    twitch_id: str
    login: str
    display_name: str
    description: str = ""
    profile_image_url: str = ""
    broadcaster_type: str = ""
    created_at: datetime | None = None
