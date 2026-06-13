from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.channel import Channel
    from app.models.chat_message import ChatMessage


class Vod(Base):
    __tablename__ = "vods"

    id: Mapped[int] = mapped_column(primary_key=True)
    twitch_vod_id: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"))
    title: Mapped[str | None] = mapped_column(String(500))
    duration_seconds: Mapped[int | None]
    stream_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published: Mapped[bool | None]
    thumbnail_url: Mapped[str | None] = mapped_column(String(500))
    chat_ingested: Mapped[bool] = mapped_column(default=False)

    channel: Mapped[Channel] = relationship(back_populates="vods")
    chat_messages: Mapped[list[ChatMessage]] = relationship(
        back_populates="vod"
    )
