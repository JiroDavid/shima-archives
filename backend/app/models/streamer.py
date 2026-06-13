from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.channel import Channel


class Streamer(Base):
    __tablename__ = "streamers"

    id: Mapped[int] = mapped_column(primary_key=True)
    twitch_id: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(50))
    access_token: Mapped[str | None] = mapped_column(Text)  # encrypted at rest
    refresh_token: Mapped[str | None] = mapped_column(Text)  # encrypted at rest
    channel_id: Mapped[int | None] = mapped_column(ForeignKey("channels.id"))

    channel: Mapped[Channel | None] = relationship(back_populates="streamer")
