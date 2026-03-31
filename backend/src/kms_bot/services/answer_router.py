"""Runtime AI provider dispatcher.

Allows switching between registered :class:`AnswerService` implementations
at runtime without restarting the server.  The router itself implements
:class:`AnswerService` and can be used as a drop-in replacement.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Literal

from kms_bot.schemas.query import AnswerGeneratorInput
from kms_bot.services.interfaces import AnswerService

logger = logging.getLogger(__name__)

ProviderName = Literal["azure_openai", "github_models"]


class ProviderAnswerRouter(AnswerService):
    """Wraps two :class:`AnswerService` instances and routes to the active one.

    Thread-safe provider switching via :meth:`set_provider`.
    """

    def __init__(
        self,
        *,
        default_provider: ProviderName,
        azure_service: AnswerService,
        github_service: AnswerService,
    ) -> None:
        self._lock = asyncio.Lock()
        self._provider: ProviderName = default_provider
        self._services: dict[str, AnswerService] = {
            "azure_openai": azure_service,
            "github_models": github_service,
        }
        logger.info("ProviderAnswerRouter initialised – default provider: %s", default_provider)

    @property
    def current_provider(self) -> ProviderName:
        return self._provider

    async def set_provider(self, provider: ProviderName) -> None:
        async with self._lock:
            if self._provider != provider:
                logger.info("AI provider switched: %s → %s", self._provider, provider)
                self._provider = provider

    async def generate_answer(self, payload: AnswerGeneratorInput) -> str:
        service = self._services[self._provider]
        return await service.generate_answer(payload)
