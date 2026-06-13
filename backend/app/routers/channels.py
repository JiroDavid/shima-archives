from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas import ClipRead, TwitchChannel, VodRead
from app.services.twitch import TwitchClient, get_twitch_client

router = APIRouter(prefix="/channel", tags=["channels"])

_NOT_IMPLEMENTED = "Not implemented yet"

TwitchDep = Annotated[TwitchClient, Depends(get_twitch_client)]


@router.get("/{username}", response_model=TwitchChannel)
async def get_channel(username: str, twitch: TwitchDep) -> TwitchChannel:
    user = await twitch.get_user(username)
    if user is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"Channel '{username}' not found"
        )
    return TwitchChannel(
        twitch_id=user["id"],
        login=user["login"],
        display_name=user["display_name"],
        description=user.get("description", ""),
        profile_image_url=user.get("profile_image_url", ""),
        broadcaster_type=user.get("broadcaster_type", ""),
        created_at=user.get("created_at"),
    )


@router.get("/{username}/vods", response_model=list[VodRead])
async def list_vods(username: str) -> list[VodRead]:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, _NOT_IMPLEMENTED)


@router.get("/{username}/clips", response_model=list[ClipRead])
async def list_clips(
    username: str,
    game: str | None = Query(default=None),
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = Query(default=None),
    sort: str = Query(default="views"),
) -> list[ClipRead]:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, _NOT_IMPLEMENTED)
