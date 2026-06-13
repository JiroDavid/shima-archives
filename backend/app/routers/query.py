from fastapi import APIRouter, HTTPException, status

from app.schemas import QueryRequest, QueryResponse

router = APIRouter(tags=["query"])


@router.post("/query", response_model=QueryResponse)
async def query_chat(payload: QueryRequest) -> QueryResponse:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented yet")
