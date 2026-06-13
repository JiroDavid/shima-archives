from fastapi import APIRouter, HTTPException, Query, status

from app.schemas import ChannelRead, ClipRead, VodRead

router = APIRouter(prefix="/channel", tags=["channels"])

_NOT_IMPLEMENTED = "Not implemented yet"


@router.get("/{username}", response_model=ChannelRead)
async def get_channel(username: str) -> ChannelRead:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, _NOT_IMPLEMENTED)


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
