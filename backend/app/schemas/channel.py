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
