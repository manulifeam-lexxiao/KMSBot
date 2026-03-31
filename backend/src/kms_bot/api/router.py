from __future__ import annotations

from fastapi import APIRouter

from kms_bot.api.routes import health, index, query, sync

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(sync.router)
api_router.include_router(index.router)
api_router.include_router(query.router)