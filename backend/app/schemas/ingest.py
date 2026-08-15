from pydantic import BaseModel


class IngestResult(BaseModel):
    channel: str
    vods_processed: int
    chunks_created: int
