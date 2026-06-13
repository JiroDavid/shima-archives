from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/twitch/callback")
async def twitch_oauth_callback(code: str, state: str | None = None) -> dict[str, str]:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented yet")
