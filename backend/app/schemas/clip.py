from datetime import datetime

from pydantic import BaseModel


class ClipRead(BaseModel):
    """Twitch clip, proxied from the Helix clips endpoint."""

    id: str
    title: str
    url: str
    thumbnail_url: str
    duration_seconds: float
    view_count: int
    creator_name: str
    game_id: str | None = None
    created_at: datetime
