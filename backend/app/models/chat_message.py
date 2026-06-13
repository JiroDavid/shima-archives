from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.channel import Channel
    from app.models.vod import Vod


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    __table_args__ = (
        Index("idx_chat_channel_user", "channel_id", "username"),
        Index("idx_chat_sent_at", "sent_at"),
        Index("idx_chat_vod", "vod_id", "vod_offset_secs"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"))
    vod_id: Mapped[int | None] = mapped_column(ForeignKey("vods.id"))
    username: Mapped[str] = mapped_column(String(50))
    message: Mapped[str] = mapped_column(Text)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    vod_offset_secs: Mapped[int | None]
    badges: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    emote_ids: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    # 'vod_replay' | 'live_bot'
    source: Mapped[str] = mapped_column(String(10))

    channel: Mapped[Channel] = relationship(back_populates="chat_messages")
    vod: Mapped[Vod | None] = relationship(back_populates="chat_messages")
