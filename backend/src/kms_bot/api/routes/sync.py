from __future__ import annotations

from fastapi import APIRouter, Depends, status

from kms_bot.core.dependencies import get_sync_service
from kms_bot.schemas.common import OperationAcceptedResponse
from kms_bot.schemas.sync import SyncStatusResponse
from kms_bot.services.interfaces import SyncService

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post(
    "/full", response_model=OperationAcceptedResponse, status_code=status.HTTP_202_ACCEPTED
)
async def trigger_full_sync(
    sync_service: SyncService = Depends(get_sync_service),
) -> OperationAcceptedResponse:
    return await sync_service.trigger_full_sync()


@router.post(
    "/incremental", response_model=OperationAcceptedResponse, status_code=status.HTTP_202_ACCEPTED
)
async def trigger_incremental_sync(
    sync_service: SyncService = Depends(get_sync_service),
) -> OperationAcceptedResponse:
    return await sync_service.trigger_incremental_sync()


@router.get("/status", response_model=SyncStatusResponse)
async def get_sync_status(
    sync_service: SyncService = Depends(get_sync_service),
) -> SyncStatusResponse:
    return await sync_service.get_status()
