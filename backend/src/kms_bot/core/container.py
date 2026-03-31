from __future__ import annotations

from dataclasses import dataclass

from kms_bot.core.settings import ApplicationSettings
from kms_bot.db.sqlite import SQLiteDatabase
from kms_bot.repositories.document_registry import DocumentRegistryRepository
from kms_bot.services.confluence_client import ConfluenceClient
from kms_bot.services.interfaces import AnswerService, ChunkService, ParseService, QueryService, SearchService, SyncService
from kms_bot.services.parser import ConfluenceParseService
from kms_bot.services.chunker import ConfluenceChunkService
from kms_bot.services.azure_search_client import AzureSearchClient
from kms_bot.services.placeholders import (
    PlaceholderAnswerService,
    PlaceholderQueryService,
    PlaceholderSearchService,
)
from kms_bot.services.search import AzureAISearchService
from kms_bot.services.sync import ConfluenceSyncService


@dataclass(slots=True)
class ServiceContainer:
    settings: ApplicationSettings
    database: SQLiteDatabase
    registry_repository: DocumentRegistryRepository
    sync_service: SyncService
    parse_service: ParseService
    chunk_service: ChunkService
    search_service: SearchService
    answer_service: AnswerService
    query_service: QueryService

    def close(self) -> None:
        return None


def build_service_container(settings: ApplicationSettings) -> ServiceContainer:
    database = SQLiteDatabase(settings)
    registry_repository = DocumentRegistryRepository(database)
    confluence_client = ConfluenceClient(settings.confluence)
    sync_service = ConfluenceSyncService(
        settings=settings,
        confluence_client=confluence_client,
        registry_repository=registry_repository,
    )
    parse_service = ConfluenceParseService(settings)
    chunk_service = ConfluenceChunkService(settings, registry_repository)
    search_service: SearchService
    if settings.search.is_configured:
        azure_client = AzureSearchClient(
            endpoint=settings.search.endpoint,
            api_key=settings.search.api_key,
            index_name=settings.search.index_name,
        )
        search_service = AzureAISearchService(
            settings=settings,
            azure_client=azure_client,
            registry_repository=registry_repository,
        )
    else:
        search_service = PlaceholderSearchService(settings, registry_repository)
    answer_service = PlaceholderAnswerService()
    query_service = PlaceholderQueryService(
        settings=settings,
        search_service=search_service,
        answer_service=answer_service,
    )

    return ServiceContainer(
        settings=settings,
        database=database,
        registry_repository=registry_repository,
        sync_service=sync_service,
        parse_service=parse_service,
        chunk_service=chunk_service,
        search_service=search_service,
        answer_service=answer_service,
        query_service=query_service,
    )