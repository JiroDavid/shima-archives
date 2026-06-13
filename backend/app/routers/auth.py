from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/twitch")
async def twitch_oauth_callback(code: str) -> dict[str, str]:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented yet")
