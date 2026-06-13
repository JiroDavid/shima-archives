from fastapi import APIRouter, HTTPException, status

from app.schemas import ChatMessageRead

router = APIRouter(prefix="/vod", tags=["vods"])

_NOT_IMPLEMENTED = "Not implemented yet"


@router.get("/{vod_id}/chat", response_model=list[ChatMessageRead])
async def get_vod_chat(vod_id: str) -> list[ChatMessageRead]:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, _NOT_IMPLEMENTED)


@router.get("/{vod_id}/stream-url")
async def get_vod_stream_url(vod_id: str) -> dict[str, str]:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, _NOT_IMPLEMENTED)
