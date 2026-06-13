from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/bot", tags=["bot"])


@router.post("/invite")
async def invite_bot() -> dict[str, str]:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented yet")
