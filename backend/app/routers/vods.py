from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.channel import Channel
from app.models.chat_message import ChatMessage
from app.models.vod import Vod
from app.schemas import TwitchVod, VodComment
from app.services.twitch import TwitchClient, get_twitch_client

router = APIRouter(tags=["vods"])

_NOT_IMPLEMENTED = "Not implemented yet"

TwitchDep = Annotated[TwitchClient, Depends(get_twitch_client)]
DbDep = Annotated[AsyncSession, Depends(get_db)]


@router.get("/vods/{user_id}", response_model=list[TwitchVod])
async def list_vods(user_id: str, twitch: TwitchDep) -> list[TwitchVod]:
    videos = await twitch.get_videos(user_id)
    return [
        TwitchVod(
            twitch_vod_id=v["id"],
            user_id=v["user_id"],
            title=v.get("title", ""),
            description=v.get("description", ""),
            url=v.get("url", ""),
            thumbnail_url=v.get("thumbnail_url", ""),
            created_at=v.get("created_at"),
            published_at=v.get("published_at"),
            duration=v.get("duration", ""),
            view_count=v.get("view_count", 0),
            type=v.get("type", "archive"),
            viewable=v.get("viewable", "public"),
        )
        for v in videos
    ]


def _to_vod_comment(message: ChatMessage) -> VodComment:
    # color isn't persisted (not part of the chat_messages schema), so replays
    # served from the DB come back without it.
    return VodComment(
        username=message.username,
        message=message.message,
        offset_seconds=float(message.vod_offset_secs or 0),
        created_at=message.sent_at,
        color="",
    )


async def _get_or_create_vod(db: AsyncSession, twitch: TwitchClient, vod_id: str) -> Vod | None:
    video = await twitch.get_video(vod_id)
    if video is None:
        return None

    channel = await db.scalar(select(Channel).where(Channel.twitch_id == video["user_id"]))
    if channel is None:
        channel = Channel(
            twitch_id=video["user_id"],
            username=video.get("user_login", ""),
            display_name=video.get("user_name"),
        )
        db.add(channel)
        await db.flush()

    vod = Vod(
        twitch_vod_id=vod_id,
        channel_id=channel.id,
        title=video.get("title"),
        thumbnail_url=video.get("thumbnail_url"),
    )
    db.add(vod)
    await db.flush()
    return vod


@router.get("/vod/{vod_id}/chat", response_model=list[VodComment])
async def get_vod_chat(vod_id: str, twitch: TwitchDep, db: DbDep) -> list[VodComment]:
    vod = await db.scalar(select(Vod).where(Vod.twitch_vod_id == vod_id))

    if vod is not None and vod.chat_ingested:
        rows = await db.scalars(
            select(ChatMessage)
            .where(ChatMessage.vod_id == vod.id, ChatMessage.source == "vod_replay")
            .order_by(ChatMessage.vod_offset_secs)
        )
        return [_to_vod_comment(row) for row in rows]

    comments = await twitch.get_vod_comments(vod_id)
    parsed = [
        VodComment(
            username=c.get("commenter", {}).get("display_name", ""),
            message=c.get("message", {}).get("body", ""),
            offset_seconds=c.get("content_offset_seconds", 0.0),
            created_at=c.get("created_at"),
            color=c.get("message", {}).get("user_color") or "",
        )
        for c in comments
    ]

    if vod is None:
        vod = await _get_or_create_vod(db, twitch, vod_id)
        if vod is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"VOD '{vod_id}' not found")

    db.add_all(
        [
            ChatMessage(
                channel_id=vod.channel_id,
                vod_id=vod.id,
                username=p.username,
                message=p.message,
                sent_at=p.created_at or vod.stream_date or datetime.now(UTC),
                vod_offset_secs=int(p.offset_seconds),
                source="vod_replay",
            )
            for p in parsed
        ]
    )
    vod.chat_ingested = True
    await db.commit()

    return parsed


@router.get("/vod/{vod_id}/stream-url")
async def get_vod_stream_url(vod_id: str) -> dict[str, str]:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, _NOT_IMPLEMENTED)
