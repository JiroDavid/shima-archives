from fastapi import APIRouter, HTTPException, status

router = APIRouter(tags=["ingest"])


@router.post("/ingest/{channel_username}", status_code=status.HTTP_202_ACCEPTED)
async def trigger_ingest(channel_username: str) -> dict[str, str]:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented yet")
