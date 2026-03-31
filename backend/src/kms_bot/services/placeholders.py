from __future__ import annotations

from kms_bot.core.errors import ModuleNotReadyError
from kms_bot.core.settings import ApplicationSettings
from kms_bot.core.utils import make_job_id, utcnow
from kms_bot.repositories.document_registry import DocumentRegistryRepository
from kms_bot.schemas.common import JobType, OperationAcceptedResponse
from kms_bot.schemas.documents import ChunkRecord, CleanedDocument
from kms_bot.schemas.index import IndexStatusResponse
from kms_bot.schemas.query import (
    AnswerGeneratorInput,
    QueryDebugInfo,
    QueryRequest,
    QueryResponse,
    QuerySource,
    RelatedDocument,
    SearchResultHit,
)
from kms_bot.schemas.sync import SyncStatusResponse
from kms_bot.services.interfaces import AnswerService, ChunkService, ParseService, QueryService, SearchService, SyncService
from kms_bot.services.query import normalize_query



class PlaceholderSyncService(SyncService):
    def __init__(self, settings: ApplicationSettings) -> None:
        self._settings = settings

    async def trigger_full_sync(self) -> OperationAcceptedResponse:
        return self._accepted_response(
            job_type="full_sync",
            job_id=make_job_id("sync-full"),
            message="Full sync request accepted by the baseline placeholder.",
        )

    async def trigger_incremental_sync(self) -> OperationAcceptedResponse:
        return self._accepted_response(
            job_type="incremental_sync",
            job_id=make_job_id("sync-incremental"),
            message="Incremental sync request accepted by the baseline placeholder.",
        )

    async def get_status(self) -> SyncStatusResponse:
        return SyncStatusResponse(
            status="idle",
            mode="none",
            current_job_id=None,
            pipeline_version=self._settings.app.pipeline_version,
            last_started_at=None,
            last_finished_at=None,
            last_success_at=None,
            processed_pages=0,
            changed_pages=0,
            error_message=None,
        )

    def _accepted_response(self, *, job_type: JobType, job_id: str, message: str) -> OperationAcceptedResponse:
        return OperationAcceptedResponse(
            job_id=job_id,
            job_type=job_type,
            status="accepted",
            requested_at=utcnow(),
            pipeline_version=self._settings.app.pipeline_version,
            message=message,
        )


class PlaceholderParseService(ParseService):
    async def parse_document(self, *, doc_id: str, title: str, raw_content: str) -> CleanedDocument:
        raise ModuleNotReadyError("parser")


class PlaceholderChunkService(ChunkService):
    async def chunk_document(self, document: CleanedDocument, *, url: str) -> list[ChunkRecord]:
        raise ModuleNotReadyError("chunker")


class PlaceholderSearchService(SearchService):
    def __init__(self, settings: ApplicationSettings, registry_repository: DocumentRegistryRepository) -> None:
        self._settings = settings
        self._registry_repository = registry_repository

    async def search(self, *, query: str, top_k: int) -> list[SearchResultHit]:
        return []

    async def rebuild_index(self) -> OperationAcceptedResponse:
        return OperationAcceptedResponse(
            job_id=make_job_id("index-rebuild"),
            job_type="index_rebuild",
            status="accepted",
            requested_at=utcnow(),
            pipeline_version=self._settings.app.pipeline_version,
            message="Index rebuild request accepted by the baseline placeholder.",
        )

    async def get_index_status(self) -> IndexStatusResponse:
        return IndexStatusResponse(
            status="idle",
            current_job_id=None,
            pipeline_version=self._settings.app.pipeline_version,
            last_started_at=None,
            last_finished_at=None,
            last_success_at=None,
            indexed_documents=0,
            indexed_chunks=0,
            error_message=None,
        )


class PlaceholderAnswerService(AnswerService):
    async def generate_answer(self, payload: AnswerGeneratorInput) -> str:
        if payload.selected_chunks:
            return "Answer generation is not implemented yet. Relevant chunks were selected by the baseline query flow."
        return "The query pipeline is wired, but search and answer modules are not implemented yet."


class PlaceholderQueryService(QueryService):
    def __init__(
        self,
        *,
        settings: ApplicationSettings,
        search_service: SearchService,
        answer_service: AnswerService,
    ) -> None:
        self._settings = settings
        self._search_service = search_service
        self._answer_service = answer_service

    async def answer_query(self, request: QueryRequest) -> QueryResponse:
        normalized_query = normalize_query(request.query)
        selected_chunks = await self._search_service.search(query=normalized_query, top_k=request.top_k)
        answer = await self._answer_service.generate_answer(
            AnswerGeneratorInput(
                query=request.query,
                normalized_query=normalized_query,
                prompt_template_path=self._settings.prompts.query_answering,
                selected_chunks=selected_chunks,
                include_debug=request.include_debug,
            )
        )
        return QueryResponse(
            answer=answer,
            sources=[self._to_source(chunk) for chunk in selected_chunks],
            related_documents=self._to_related_documents(selected_chunks),
            debug=QueryDebugInfo(
                normalized_query=normalized_query,
                selected_chunks=selected_chunks if request.include_debug else [],
            ),
        )

    @staticmethod
    def _to_source(chunk: SearchResultHit) -> QuerySource:
        return QuerySource(
            title=chunk.title,
            url=chunk.url,
            section=chunk.section,
            doc_id=chunk.doc_id,
            chunk_id=chunk.chunk_id,
        )

    @staticmethod
    def _to_related_documents(selected_chunks: list[SearchResultHit]) -> list[RelatedDocument]:
        related_documents: dict[str, RelatedDocument] = {}
        for chunk in selected_chunks:
            related_documents.setdefault(
                chunk.doc_id,
                RelatedDocument(page_id=chunk.doc_id, title=chunk.title, url=chunk.url),
            )
        return list(related_documents.values())