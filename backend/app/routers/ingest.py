from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.channel import Channel
from app.models.chat_message import ChatMessage
from app.models.vod import Vod
from app.schemas import IngestResult
from app.services.chunking import chunk_messages
from app.services.embeddings import EmbeddingClient, get_embedding_client
from app.services.twitch import TwitchClient, get_twitch_client
from app.services.vectorstore import ChromaStore, get_chroma_store

router = APIRouter(tags=["ingest"])

TwitchDep = Annotated[TwitchClient, Depends(get_twitch_client)]
DbDep = Annotated[AsyncSession, Depends(get_db)]
EmbedDep = Annotated[EmbeddingClient, Depends(get_embedding_client)]
StoreDep = Annotated[ChromaStore, Depends(get_chroma_store)]


@router.post("/ingest/{channel_username}", response_model=IngestResult)
async def trigger_ingest(
    channel_username: str,
    twitch: TwitchDep,
    db: DbDep,
    embedder: EmbedDep,
    store: StoreDep,
) -> IngestResult:
    """Chunk and embed persisted VOD chat replay into Chroma for the given channel.

    Only VODs whose chat has already been replayed into Postgres
    (``chat_ingested``) and not yet chunked (``chunks_ingested``) are
    processed; this endpoint never talks to Twitch beyond resolving the
    channel.
    """
    user = await twitch.get_user(channel_username)
    if user is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"Channel '{channel_username}' not found"
        )

    channel = await db.scalar(select(Channel).where(Channel.twitch_id == user["id"]))
    if channel is None:
        return IngestResult(channel=channel_username, vods_processed=0, chunks_created=0)

    vods = (
        await db.scalars(
            select(Vod).where(
                Vod.channel_id == channel.id,
                Vod.chat_ingested.is_(True),
                Vod.chunks_ingested.is_(False),
            )
        )
    ).all()

    chunks_created = 0
    for vod in vods:
        messages = (
            await db.scalars(
                select(ChatMessage)
                .where(ChatMessage.vod_id == vod.id)
                .order_by(ChatMessage.vod_offset_secs)
            )
        ).all()
        chunks = chunk_messages(
            list(messages), vod_id=vod.id, channel_id=channel.id, twitch_vod_id=vod.twitch_vod_id
        )
        if chunks:
            embeddings = await embedder.embed_texts([c.text for c in chunks])
            store.upsert_chunks(chunks, embeddings)
            chunks_created += len(chunks)
        vod.chunks_ingested = True

    await db.commit()

    return IngestResult(
        channel=channel_username, vods_processed=len(vods), chunks_created=chunks_created
    )
