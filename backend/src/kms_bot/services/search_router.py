"""Runtime search provider router.

Mirrors the ProviderAnswerRouter pattern: wraps two SearchService
implementations and routes to the active one, allowing runtime switching
without restarting the server.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Literal

from kms_bot.schemas.common import OperationAcceptedResponse
from kms_bot.schemas.index import IndexStatusResponse
from kms_bot.schemas.query import SearchResultHit
from kms_bot.services.interfaces import SearchService

logger = logging.getLogger(__name__)

SearchProviderName = Literal["sqlite_fts5", "azure_ai_search"]


class SearchProviderRouter(SearchService):
    """Wraps two SearchService instances and routes to the active one."""

    def __init__(
        self,
        *,
        default_provider: SearchProviderName,
        sqlite_service: SearchService,
        azure_service: SearchService,
    ) -> None:
        self._lock = asyncio.Lock()
        self._provider: SearchProviderName = default_provider
        self._services: dict[str, SearchService] = {
            "sqlite_fts5": sqlite_service,
            "azure_ai_search": azure_service,
        }
        logger.info("SearchProviderRouter initialised – default provider: %s", default_provider)

    @property
    def current_provider(self) -> SearchProviderName:
        return self._provider

    async def set_provider(self, provider: SearchProviderName) -> None:
        async with self._lock:
            if self._provider != provider:
                logger.info("Search provider switched: %s → %s", self._provider, provider)
                self._provider = provider

    async def search(self, *, query: str, top_k: int) -> list[SearchResultHit]:
        service = self._services[self._provider]
        return await service.search(query=query, top_k=top_k)

    async def rebuild_index(self) -> OperationAcceptedResponse:
        service = self._services[self._provider]
        return await service.rebuild_index()

    async def get_index_status(self) -> IndexStatusResponse:
        service = self._services[self._provider]
        return await service.get_index_status()
