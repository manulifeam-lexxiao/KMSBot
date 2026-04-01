"""Settings API routes.

Provides endpoints to inspect and change runtime configuration,
such as the active AI provider, token usage stats, and THINKING mode settings.
"""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from kms_bot.core.dependencies import get_answer_router, get_settings, get_token_usage_repository
from kms_bot.core.settings import ApplicationSettings
from kms_bot.repositories.token_usage import TokenUsageRepository
from kms_bot.services.answer_router import ProviderAnswerRouter

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
