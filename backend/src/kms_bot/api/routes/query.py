from __future__ import annotations

from fastapi import APIRouter, Depends

from kms_bot.core.dependencies import get_query_service
from kms_bot.schemas.query import QueryRequest, QueryResponse
from kms_bot.services.interfaces import QueryService

router = APIRouter(prefix="/query", tags=["query"])


@router.post("", response_model=QueryResponse)
async def submit_query(
    request: QueryRequest,
    query_service: QueryService = Depends(get_query_service),
) -> QueryResponse:
    return await query_service.answer_query(request)
