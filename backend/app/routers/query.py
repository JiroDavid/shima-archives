from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.channel import Channel
from app.schemas import QueryRequest, QueryResponse, QuerySource
from app.services.embeddings import EmbeddingClient, get_embedding_client
from app.services.llm import GeminiClient, get_gemini_client
from app.services.vectorstore import ChromaStore, ChunkMatch, get_chroma_store

router = APIRouter(tags=["query"])

DbDep = Annotated[AsyncSession, Depends(get_db)]
EmbedDep = Annotated[EmbeddingClient, Depends(get_embedding_client)]
StoreDep = Annotated[ChromaStore, Depends(get_chroma_store)]
LlmDep = Annotated[GeminiClient, Depends(get_gemini_client)]

_NO_MATCH_ANSWER = "I couldn't find anything relevant in the chat history."

_PROMPT_TEMPLATE = (
    "You are answering a question about a Twitch streamer's chat history using "
    "the chat log excerpts below. Answer concisely using only this context; if "
    "the answer isn't in the context, say you don't know.\n\n"
    "Context:\n{context}\n\nQuestion: {question}\nAnswer:"
)


def _build_prompt(question: str, matches: list[ChunkMatch]) -> str:
    context = "\n\n".join(
        f"[VOD {m.twitch_vod_id} @ {m.start_offset_secs}s]\n{m.text}" for m in matches
    )
    return _PROMPT_TEMPLATE.format(context=context, question=question)


@router.post("/query", response_model=QueryResponse)
async def query_chat(
    payload: QueryRequest, db: DbDep, embedder: EmbedDep, store: StoreDep, llm: LlmDep
) -> QueryResponse:
    channel_id: int | None = None
    if payload.channel is not None:
        channel = await db.scalar(select(Channel).where(Channel.username == payload.channel))
        if channel is None:
            return QueryResponse(answer=_NO_MATCH_ANSWER, sources=[])
        channel_id = channel.id

    [embedding] = await embedder.embed_texts([payload.question])
    matches = store.query_chunks(
        embedding,
        top_k=payload.top_k,
        channel_id=channel_id,
        twitch_vod_id=payload.vod_id,
    )

    if not matches:
        return QueryResponse(answer=_NO_MATCH_ANSWER, sources=[])

    answer = await llm.generate(_build_prompt(payload.question, matches))

    return QueryResponse(
        answer=answer,
        sources=[
            QuerySource(
                vod_id=m.twitch_vod_id,
                vod_offset_secs=m.start_offset_secs,
                message_preview=m.text,
            )
            for m in matches
        ],
    )
