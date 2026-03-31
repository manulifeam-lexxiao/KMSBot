from __future__ import annotations

from fastapi import APIRouter, Depends, status

from kms_bot.core.dependencies import get_search_service
from kms_bot.schemas.common import OperationAcceptedResponse
from kms_bot.schemas.index import IndexStatusResponse
from kms_bot.services.interfaces import SearchService

router = APIRouter(prefix="/index", tags=["index"])


@router.post(
    "/rebuild", response_model=OperationAcceptedResponse, status_code=status.HTTP_202_ACCEPTED
)
async def trigger_index_rebuild(
    search_service: SearchService = Depends(get_search_service),
) -> OperationAcceptedResponse:
    return await search_service.rebuild_index()


@router.get("/status", response_model=IndexStatusResponse)
async def get_index_status(
    search_service: SearchService = Depends(get_search_service),
) -> IndexStatusResponse:
    return await search_service.get_index_status()
