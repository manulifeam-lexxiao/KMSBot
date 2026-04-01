"""Settings API routes.

Provides endpoints to inspect and change runtime configuration,
such as the active AI provider, token usage stats, and THINKING mode settings.
"""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from kms_bot.core.dependencies import (
    get_answer_router,
    get_search_router,
    get_settings,
    get_token_usage_repository,
)
from kms_bot.core.settings import ApplicationSettings
from kms_bot.repositories.token_usage import TokenUsageRepository
from kms_bot.services.answer_router import ProviderAnswerRouter
from kms_bot.services.search_router import SearchProviderRouter

router = APIRouter(prefix="/settings", tags=["settings"])


class ProviderResponse(BaseModel):
    provider: str
    available_providers: list[str] = ["azure_openai", "github_models"]


class SetProviderRequest(BaseModel):
    provider: Literal["azure_openai", "github_models"]


class ThinkingSettingsResponse(BaseModel):
    thinking_max_articles: int


class SetThinkingSettingsRequest(BaseModel):
    thinking_max_articles: int = Field(ge=1, le=50)


class QuerySettingsResponse(BaseModel):
    top_k: int
    max_chunks_per_doc: int
    similarity_threshold: float


class SetQuerySettingsRequest(BaseModel):
    top_k: int | None = Field(default=None, ge=1, le=10)
    max_chunks_per_doc: int | None = Field(default=None, ge=1, le=10)
    similarity_threshold: float | None = Field(default=None, ge=0.0, le=1.0)


class SearchProviderResponse(BaseModel):
    provider: str
    available_providers: list[str] = ["sqlite_fts5", "azure_ai_search"]
    azure_configured: bool


class SetSearchProviderRequest(BaseModel):
    provider: Literal["sqlite_fts5", "azure_ai_search"]


class ConfluenceStatusResponse(BaseModel):
    configured: bool
    base_url: str | None
    space_key: str | None
    page_limit: int | None
    connectivity: Literal["ok", "error", "not_configured"]
    error_detail: str | None = None


@router.get("/provider", response_model=ProviderResponse)
async def get_provider(
    answer_router: ProviderAnswerRouter = Depends(get_answer_router),
) -> ProviderResponse:
    """Return the currently active AI provider."""
    return ProviderResponse(provider=answer_router.current_provider)


@router.patch("/provider", response_model=ProviderResponse)
async def set_provider(
    body: SetProviderRequest,
    answer_router: ProviderAnswerRouter = Depends(get_answer_router),
) -> ProviderResponse:
    """Switch the active AI provider at runtime."""
    await answer_router.set_provider(body.provider)
    return ProviderResponse(provider=answer_router.current_provider)


@router.get("/token-usage")
async def get_token_usage(
    token_repo: TokenUsageRepository = Depends(get_token_usage_repository),
) -> dict[str, Any]:
    """Return token usage statistics."""
    return token_repo.get_summary()


@router.get("/thinking", response_model=ThinkingSettingsResponse)
async def get_thinking_settings(
    settings: ApplicationSettings = Depends(get_settings),
) -> ThinkingSettingsResponse:
    """Return current THINKING mode settings."""
    return ThinkingSettingsResponse(
        thinking_max_articles=settings.query.thinking_max_articles,
    )


@router.patch("/thinking", response_model=ThinkingSettingsResponse)
async def set_thinking_settings(
    body: SetThinkingSettingsRequest,
    settings: ApplicationSettings = Depends(get_settings),
) -> ThinkingSettingsResponse:
    """Update THINKING mode settings at runtime."""
    settings.query.thinking_max_articles = body.thinking_max_articles
    return ThinkingSettingsResponse(
        thinking_max_articles=settings.query.thinking_max_articles,
    )


@router.get("/query", response_model=QuerySettingsResponse)
async def get_query_settings(
    settings: ApplicationSettings = Depends(get_settings),
) -> QuerySettingsResponse:
    """Return current query settings."""
    return QuerySettingsResponse(
        top_k=settings.query.top_k,
        max_chunks_per_doc=settings.query.max_chunks_per_doc,
        similarity_threshold=settings.query.similarity_threshold,
    )


@router.patch("/query", response_model=QuerySettingsResponse)
async def set_query_settings(
    body: SetQuerySettingsRequest,
    settings: ApplicationSettings = Depends(get_settings),
) -> QuerySettingsResponse:
    """Update query parameters at runtime."""
    if body.top_k is not None:
        settings.query.top_k = body.top_k
    if body.max_chunks_per_doc is not None:
        settings.query.max_chunks_per_doc = body.max_chunks_per_doc
    if body.similarity_threshold is not None:
        settings.query.similarity_threshold = body.similarity_threshold
    return QuerySettingsResponse(
        top_k=settings.query.top_k,
        max_chunks_per_doc=settings.query.max_chunks_per_doc,
        similarity_threshold=settings.query.similarity_threshold,
    )


@router.get("/search-provider", response_model=SearchProviderResponse)
async def get_search_provider(
    settings: ApplicationSettings = Depends(get_settings),
    search_router: SearchProviderRouter = Depends(get_search_router),
) -> SearchProviderResponse:
    """Return the currently active search provider."""
    return SearchProviderResponse(
        provider=search_router.current_provider,
        azure_configured=settings.search.is_configured,
    )


@router.patch("/search-provider", response_model=SearchProviderResponse)
async def set_search_provider(
    body: SetSearchProviderRequest,
    settings: ApplicationSettings = Depends(get_settings),
    search_router: SearchProviderRouter = Depends(get_search_router),
) -> SearchProviderResponse:
    """Switch the active search provider at runtime."""
    if body.provider == "azure_ai_search" and not settings.search.is_configured:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=400,
            detail="Azure AI Search is not configured. Please set endpoint, api_key and index_name.",
        )
    await search_router.set_provider(body.provider)
    return SearchProviderResponse(
        provider=search_router.current_provider,
        azure_configured=settings.search.is_configured,
    )


@router.get("/confluence", response_model=ConfluenceStatusResponse)
async def get_confluence_status(
    settings: ApplicationSettings = Depends(get_settings),
) -> ConfluenceStatusResponse:
    """Return Confluence configuration status and basic connectivity check."""
    cfg = settings.confluence
    if not cfg.is_configured:
        return ConfluenceStatusResponse(
            configured=False,
            base_url=None,
            space_key=None,
            page_limit=None,
            connectivity="not_configured",
        )

    import httpx

    connectivity: Literal["ok", "error", "not_configured"] = "ok"
    error_detail: str | None = None
    try:
        async with httpx.AsyncClient(
            auth=(cfg.username, cfg.api_token),
            timeout=5.0,
        ) as client:
            resp = await client.get(f"{cfg.base_url.rstrip('/')}/rest/api/space/{cfg.space_key}")
            if resp.status_code >= 400:
                connectivity = "error"
                error_detail = f"HTTP {resp.status_code}"
    except Exception as exc:
        connectivity = "error"
        error_detail = str(exc)

    return ConfluenceStatusResponse(
        configured=True,
        base_url=cfg.base_url,
        space_key=cfg.space_key,
        page_limit=cfg.page_limit,
        connectivity=connectivity,
        error_detail=error_detail,
    )
