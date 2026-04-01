from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from kms_bot.core.dependencies import get_query_service
from kms_bot.schemas.query import QueryRequest, QueryResponse
from kms_bot.services.interfaces import QueryService
from kms_bot.services.query import QueryOrchestratorService

router = APIRouter(prefix="/query", tags=["query"])


@router.post("", response_model=QueryResponse)
async def submit_query(
    request: QueryRequest,
    query_service: QueryService = Depends(get_query_service),
) -> QueryResponse | StreamingResponse:
    # THINKING 模式使用 SSE 流式响应
    if request.thinking and isinstance(query_service, QueryOrchestratorService):

        async def event_generator():
            async for event in query_service.answer_query_streaming(request):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    return await query_service.answer_query(request)
