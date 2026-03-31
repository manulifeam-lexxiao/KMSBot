"""Azure AI Search service – implements the SearchService interface.

Responsibilities:
- BM25 keyword search against the Azure AI Search index
- Index rebuild from chunk artifacts on disk
- Index status reporting

This module consumes only the frozen chunk contract and exposes
``SearchResultHit`` objects that the query orchestrator can use
without knowing Azure SDK internals.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from kms_bot.core.settings import ApplicationSettings
from kms_bot.core.utils import make_job_id, utcnow
from kms_bot.repositories.document_registry import DocumentRegistryRepository
from kms_bot.schemas.common import OperationAcceptedResponse
from kms_bot.schemas.documents import ChunkRecord
from kms_bot.schemas.index import IndexStatusResponse
from kms_bot.schemas.query import SearchResultHit
from kms_bot.services.azure_search_client import AzureSearchClient
from kms_bot.services.interfaces import SearchService

logger = logging.getLogger(__name__)

UPLOAD_BATCH_SIZE = 500
"""Maximum documents per Azure upload call."""


class _IndexState:
    """In-memory tracker for the latest index rebuild status."""

    def __init__(self, pipeline_version: int) -> None:
        self.status: str = "idle"
        self.current_job_id: str | None = None
        self.pipeline_version: int = pipeline_version
        self.last_started_at: datetime | None = None
        self.last_finished_at: datetime | None = None
        self.last_success_at: datetime | None = None
        self.indexed_documents: int = 0
        self.indexed_chunks: int = 0
        self.error_message: str | None = None

    def to_response(self) -> IndexStatusResponse:
        return IndexStatusResponse(
            status=self.status,
            current_job_id=self.current_job_id,
            pipeline_version=self.pipeline_version,
            last_started_at=self.last_started_at,
            last_finished_at=self.last_finished_at,
            last_success_at=self.last_success_at,
            indexed_documents=self.indexed_documents,
            indexed_chunks=self.indexed_chunks,
            error_message=self.error_message,
        )


class AzureAISearchService(SearchService):
    """Real Azure AI Search implementation using BM25 keyword retrieval."""

    def __init__(
        self,
        *,
        settings: ApplicationSettings,
        azure_client: AzureSearchClient,
        registry_repository: DocumentRegistryRepository,
    ) -> None:
        self._settings = settings
        self._client = azure_client
        self._registry = registry_repository
        self._chunks_dir: Path = settings.resolve_path(settings.storage.chunks_dir)
        self._state = _IndexState(settings.app.pipeline_version)
        self._lock = asyncio.Lock()

    # ── SearchService.search ──────────────────────────────────

    async def search(self, *, query: str, top_k: int) -> list[SearchResultHit]:
        raw_hits = await asyncio.to_thread(
            self._client.search,
            query,
            top=top_k,
        )
        hits: list[SearchResultHit] = []
        for raw in raw_hits:
            hits.append(self._to_search_result_hit(raw))
        logger.info(
            "search_completed",
            extra={"query": query, "top_k": top_k, "hits": len(hits)},
        )
        return hits

    # ── SearchService.rebuild_index ───────────────────────────

    async def rebuild_index(self) -> OperationAcceptedResponse:
        if self._state.status == "running":
            return OperationAcceptedResponse(
                job_id=self._state.current_job_id or "unknown",
                job_type="index_rebuild",
                status="accepted",
                requested_at=utcnow(),
                pipeline_version=self._settings.app.pipeline_version,
                message="Index rebuild is already running.",
            )

        job_id = make_job_id("index-rebuild")
        asyncio.create_task(self._run_rebuild(job_id))
        return OperationAcceptedResponse(
            job_id=job_id,
            job_type="index_rebuild",
            status="accepted",
            requested_at=utcnow(),
            pipeline_version=self._settings.app.pipeline_version,
            message="Index rebuild request accepted.",
        )

    # ── SearchService.get_index_status ────────────────────────

    async def get_index_status(self) -> IndexStatusResponse:
        return self._state.to_response()

    # ── background rebuild ────────────────────────────────────

    async def _run_rebuild(self, job_id: str) -> None:
        async with self._lock:
            self._state.status = "running"
            self._state.current_job_id = job_id
            self._state.last_started_at = utcnow()
            self._state.error_message = None

            try:
                # 1. Recreate index
                await asyncio.to_thread(self._client.delete_index)
                await asyncio.to_thread(self._client.create_or_update_index)

                # 2. Load all chunk files
                all_chunks = self._load_all_chunks()

                # 3. Upload in batches
                total_uploaded = 0
                doc_ids: set[str] = set()
                for batch_start in range(0, len(all_chunks), UPLOAD_BATCH_SIZE):
                    batch = all_chunks[batch_start : batch_start + UPLOAD_BATCH_SIZE]
                    docs = [self._chunk_to_index_doc(c) for c in batch]
                    uploaded = await asyncio.to_thread(self._client.upload_documents, docs)
                    total_uploaded += uploaded
                    for c in batch:
                        doc_ids.add(c.doc_id)

                # 4. Update registry
                now = utcnow().isoformat()
                for doc_id in doc_ids:
                    self._registry.update_index_status(
                        page_id=doc_id,
                        index_status="indexed",
                        last_index_time=now,
                    )

                self._state.indexed_documents = len(doc_ids)
                self._state.indexed_chunks = total_uploaded
                self._state.status = "success"
                self._state.last_success_at = utcnow()
                logger.info(
                    "index_rebuild_completed",
                    extra={
                        "job_id": job_id,
                        "documents": len(doc_ids),
                        "chunks": total_uploaded,
                    },
                )
            except Exception as exc:
                self._state.status = "error"
                self._state.error_message = str(exc)
                logger.error(
                    "index_rebuild_failed",
                    extra={"job_id": job_id, "error": str(exc)},
                    exc_info=True,
                )
            finally:
                self._state.last_finished_at = utcnow()

    # ── helpers ───────────────────────────────────────────────

    def _load_all_chunks(self) -> list[ChunkRecord]:
        """Read every ``*.chunks.json`` file from the chunks directory."""
        chunks: list[ChunkRecord] = []
        if not self._chunks_dir.exists():
            logger.info("chunks_dir_missing", extra={"path": str(self._chunks_dir)})
            return chunks

        for chunk_file in sorted(self._chunks_dir.glob("*.chunks.json")):
            try:
                raw = json.loads(chunk_file.read_text(encoding="utf-8"))
                for item in raw:
                    chunks.append(ChunkRecord.model_validate(item))
            except Exception as exc:
                logger.warning(
                    "chunk_file_load_error",
                    extra={"file": str(chunk_file), "error": str(exc)},
                )
        logger.info("chunks_loaded", extra={"total": len(chunks)})
        return chunks

    @staticmethod
    def _chunk_to_index_doc(chunk: ChunkRecord) -> dict[str, Any]:
        """Convert a ChunkRecord to the dict shape expected by the Azure index."""
        return {
            "chunk_id": chunk.chunk_id,
            "doc_id": chunk.doc_id,
            "title": chunk.title,
            "section": chunk.section,
            "content": chunk.content,
            "tags": chunk.tags,
            "url": str(chunk.url),
            "last_updated": utcnow().isoformat(),
            "pipeline_version": chunk.pipeline_version,
        }

    @staticmethod
    def _to_search_result_hit(raw: dict[str, Any]) -> SearchResultHit:
        """Convert a raw Azure result dict to the adapter contract."""
        return SearchResultHit(
            chunk_id=raw["chunk_id"],
            doc_id=raw["doc_id"],
            title=raw["title"],
            section=raw["section"],
            content=raw["content"],
            url=raw.get("url", "https://unknown"),
            tags=raw.get("tags", []),
            pipeline_version=raw.get("pipeline_version", 1),
            score=raw.get("score", 0.0),
        )
