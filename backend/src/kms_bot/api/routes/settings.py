"""Settings API routes.

Provides endpoints to inspect and change runtime configuration,
such as the active AI provider.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from kms_bot.core.dependencies import get_answer_router
from kms_bot.services.answer_router import ProviderAnswerRouter

router = APIRouter(prefix="/settings", tags=["settings"])


class ProviderResponse(BaseModel):
    provider: str
    available_providers: list[str] = ["azure_openai", "github_models"]


class SetProviderRequest(BaseModel):
    provider: Literal["azure_openai", "github_models"]


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
