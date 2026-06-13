from fastapi import APIRouter

from app.routers import auth, bot, channels, ingest, query, vods

api_router = APIRouter()
api_router.include_router(channels.router)
api_router.include_router(vods.router)
api_router.include_router(query.router)
api_router.include_router(ingest.router)
api_router.include_router(auth.router)
api_router.include_router(bot.router)

__all__ = ["api_router"]
