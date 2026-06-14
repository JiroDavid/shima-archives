from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas import ChatMessageRead, TwitchVod
from app.services.twitch import TwitchClient, get_twitch_client

router = APIRouter(tags=["vods"])

_NOT_IMPLEMENTED = "Not implemented yet"

TwitchDep = Annotated[TwitchClient, Depends(get_twitch_client)]


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


@router.get("/vod/{vod_id}/chat", response_model=list[ChatMessageRead])
async def get_vod_chat(vod_id: str) -> list[ChatMessageRead]:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, _NOT_IMPLEMENTED)


@router.get("/vod/{vod_id}/stream-url")
async def get_vod_stream_url(vod_id: str) -> dict[str, str]:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, _NOT_IMPLEMENTED)
