from pydantic import BaseModel


class QueryRequest(BaseModel):
    question: str
    channel: str | None = None
    vod_id: str | None = None
    top_k: int = 8


class QuerySource(BaseModel):
    vod_id: str
    vod_offset_secs: int
    message_preview: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[QuerySource]
