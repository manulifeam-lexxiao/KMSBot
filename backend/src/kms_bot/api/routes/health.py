from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from kms_bot.core.container import ServiceContainer
from kms_bot.core.dependencies import get_container, get_settings
from kms_bot.core.settings import ApplicationSettings
from kms_bot.schemas.health import HealthDependencies, HealthResponse
from kms_bot.services.search import AzureAISearchService

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def get_health(
    settings: ApplicationSettings = Depends(get_settings),
    container: ServiceContainer = Depends(get_container),
) -> HealthResponse:
    sqlite_status = "ok" if container.database.ping() else "error"

    if not settings.search.is_configured:
        azure_search_status = "not_configured"
    elif isinstance(container.search_service, AzureAISearchService):
        azure_search_status = "ok" if container.search_service._client.ping() else "error"
    else:
        azure_search_status = "degraded"
    azure_openai_status = "degraded" if settings.answer.is_configured else "not_configured"

    if sqlite_status == "error":
        overall_status = "error"
    elif "degraded" in {azure_search_status, azure_openai_status}:
        overall_status = "degraded"
    else:
        overall_status = "ok"

    return HealthResponse(
        status=overall_status,
        service="kms-bot-backend",
        version=settings.app.version,
        timestamp=datetime.now(timezone.utc),
        dependencies=HealthDependencies(
            sqlite=sqlite_status,
            azure_ai_search=azure_search_status,
            azure_openai=azure_openai_status,
        ),
    )
