from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from kms_bot.core.container import ServiceContainer
from kms_bot.core.dependencies import get_container, get_settings
from kms_bot.core.settings import ApplicationSettings
from kms_bot.schemas.health import HealthDependencies, HealthResponse
from kms_bot.services.search import AzureAISearchService
from kms_bot.services.search_router import SearchProviderRouter
from kms_bot.services.sqlite_fts_search import SQLiteFTSSearchService

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def get_health(
    settings: ApplicationSettings = Depends(get_settings),
    container: ServiceContainer = Depends(get_container),
) -> HealthResponse:
    sqlite_status = "ok" if container.database.ping() else "error"

    search_backend = settings.search.provider
    # container.search_service 是 SearchProviderRouter，需要取实际路由到的服务来判断
    active_search_svc = (
        container.search_service._services.get(container.search_service.current_provider)
        if isinstance(container.search_service, SearchProviderRouter)
        else container.search_service
    )
    if search_backend == "sqlite_fts5":
        azure_search_status = (
            "ok" if isinstance(active_search_svc, SQLiteFTSSearchService) else "degraded"
        )
    elif not settings.search.is_configured:
        azure_search_status = "not_configured"
    elif isinstance(active_search_svc, AzureAISearchService):
        azure_search_status = "ok" if active_search_svc._client.ping() else "error"
    else:
        azure_search_status = "degraded"
    azure_openai_status = "ok" if settings.answer.is_configured else "not_configured"

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
            search_backend=search_backend,
        ),
    )
