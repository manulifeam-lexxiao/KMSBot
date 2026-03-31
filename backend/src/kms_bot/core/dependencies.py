from __future__ import annotations

from fastapi import Depends, Request

from kms_bot.core.container import ServiceContainer
from kms_bot.core.settings import ApplicationSettings
from kms_bot.services.answer_router import ProviderAnswerRouter
from kms_bot.services.interfaces import AnswerService, ChunkService, ParseService, QueryService, SearchService, SyncService


def get_settings(request: Request) -> ApplicationSettings:
    return request.app.state.settings


def get_container(request: Request) -> ServiceContainer:
    return request.app.state.container


def get_sync_service(container: ServiceContainer = Depends(get_container)) -> SyncService:
    return container.sync_service


def get_parse_service(container: ServiceContainer = Depends(get_container)) -> ParseService:
    return container.parse_service


def get_chunk_service(container: ServiceContainer = Depends(get_container)) -> ChunkService:
    return container.chunk_service


def get_search_service(container: ServiceContainer = Depends(get_container)) -> SearchService:
    return container.search_service


def get_answer_service(container: ServiceContainer = Depends(get_container)) -> AnswerService:
    return container.answer_service


def get_query_service(container: ServiceContainer = Depends(get_container)) -> QueryService:
    return container.query_service


def get_answer_router(container: ServiceContainer = Depends(get_container)) -> ProviderAnswerRouter:
    return container.answer_router