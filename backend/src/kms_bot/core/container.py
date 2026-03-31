from __future__ import annotations

from dataclasses import dataclass

from kms_bot.core.settings import ApplicationSettings
from kms_bot.db.sqlite import SQLiteDatabase
from kms_bot.repositories.document_registry import DocumentRegistryRepository
from kms_bot.services.answer import AzureOpenAIAnswerService, GithubModelsAnswerService
from kms_bot.services.answer_router import ProviderAnswerRouter
from kms_bot.services.azure_search_client import AzureSearchClient
from kms_bot.services.chunker import ConfluenceChunkService
from kms_bot.services.confluence_client import ConfluenceClient
from kms_bot.services.github_models_client import GithubModelsClient
from kms_bot.services.interfaces import (
    AnswerService,
    ChunkService,
    ParseService,
    QueryService,
    SearchService,
    SyncService,
)
from kms_bot.services.openai_client import AzureOpenAIClient
from kms_bot.services.parser import ConfluenceParseService
from kms_bot.services.placeholders import (
    PlaceholderAnswerService,
    PlaceholderSearchService,
)
from kms_bot.services.query import QueryOrchestratorService
from kms_bot.services.search import AzureAISearchService
from kms_bot.services.sqlite_fts_search import SQLiteFTSSearchService
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
    answer_router: ProviderAnswerRouter
    query_service: QueryService

    def post_initialize(self) -> None:
        """在 database.initialize() 之后调用，完成需要 DB 存在的服务初始化。"""
        if isinstance(self.search_service, SQLiteFTSSearchService):
            self.search_service.initialize_table()

    def close(self) -> None:
        return None


def build_service_container(settings: ApplicationSettings) -> ServiceContainer:
    database = SQLiteDatabase(settings)
    registry_repository = DocumentRegistryRepository(database)
    confluence_client = ConfluenceClient(settings.confluence)
    parse_service = ConfluenceParseService(settings)
    chunk_service = ConfluenceChunkService(settings, registry_repository)
    sync_service = ConfluenceSyncService(
        settings=settings,
        confluence_client=confluence_client,
        registry_repository=registry_repository,
        parse_service=parse_service,
        chunk_service=chunk_service,
    )
    search_service: SearchService
    if settings.search.provider == "sqlite_fts5":
        search_service = SQLiteFTSSearchService(
            settings=settings,
            database=database,
            registry_repository=registry_repository,
        )
    elif settings.search.is_configured:
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

    # Build answer services for each supported provider
    azure_answer: AnswerService
    if settings.answer.is_configured:
        openai_client = AzureOpenAIClient(
            endpoint=settings.answer.endpoint,
            api_key=settings.answer.api_key,
            chat_deployment=settings.answer.chat_deployment,
        )
        azure_answer = AzureOpenAIAnswerService(settings=settings, openai_client=openai_client)
    else:
        azure_answer = PlaceholderAnswerService()

    github_answer: AnswerService
    if settings.github_models.is_configured:
        github_client = GithubModelsClient(
            api_token=settings.github_models.api_token,
            model_name=settings.github_models.model_name,
        )
        github_answer = GithubModelsAnswerService(settings=settings, github_client=github_client)
    else:
        github_answer = PlaceholderAnswerService()

    answer_router = ProviderAnswerRouter(
        default_provider=settings.answer.provider,
        azure_service=azure_answer,
        github_service=github_answer,
    )

    query_service = QueryOrchestratorService(
        settings=settings,
        search_service=search_service,
        answer_service=answer_router,
    )

    return ServiceContainer(
        settings=settings,
        database=database,
        registry_repository=registry_repository,
        sync_service=sync_service,
        parse_service=parse_service,
        chunk_service=chunk_service,
        search_service=search_service,
        answer_service=answer_router,
        answer_router=answer_router,
        query_service=query_service,
    )
