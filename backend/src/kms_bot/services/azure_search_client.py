"""Low-level wrapper around the Azure AI Search SDK.

This module isolates all Azure SDK imports and wire details so that the
rest of the application only interacts with plain dicts / Pydantic models.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError, ResourceNotFoundError
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SimpleField,
)

logger = logging.getLogger(__name__)

# ── index schema ──────────────────────────────────────────────

_INDEX_FIELDS: list[SearchField] = [
    SimpleField(
        name="chunk_id",
        type=SearchFieldDataType.String,
        key=True,
        filterable=True,
    ),
    SimpleField(
        name="doc_id",
        type=SearchFieldDataType.String,
        filterable=True,
    ),
    SearchableField(
        name="title",
        type=SearchFieldDataType.String,
    ),
    SearchableField(
        name="section",
        type=SearchFieldDataType.String,
    ),
    SearchableField(
        name="content",
        type=SearchFieldDataType.String,
    ),
    SimpleField(
        name="tags",
        type=SearchFieldDataType.Collection(SearchFieldDataType.String),
        filterable=True,
    ),
    SimpleField(
        name="url",
        type=SearchFieldDataType.String,
    ),
    SimpleField(
        name="last_updated",
        type=SearchFieldDataType.DateTimeOffset,
        filterable=True,
        sortable=True,
    ),
    SimpleField(
        name="pipeline_version",
        type=SearchFieldDataType.Int32,
        filterable=True,
    ),
]


@dataclass(frozen=True, slots=True)
class IndexStats:
    document_count: int
    storage_size_bytes: int


class AzureSearchClient:
    """Thin wrapper around Azure AI Search SDK clients."""

    def __init__(self, *, endpoint: str, api_key: str, index_name: str) -> None:
        self._endpoint = endpoint
        self._index_name = index_name
        credential = AzureKeyCredential(api_key)
        self._index_client = SearchIndexClient(
            endpoint=endpoint,
            credential=credential,
        )
        self._search_client = SearchClient(
            endpoint=endpoint,
            index_name=index_name,
            credential=credential,
        )

    # ── index management ──────────────────────────────────────

    def create_or_update_index(self) -> None:
        """Create or update the search index with the predefined schema."""
        index = SearchIndex(name=self._index_name, fields=_INDEX_FIELDS)
        self._index_client.create_or_update_index(index)
        logger.info("index_created_or_updated", extra={"index": self._index_name})

    def delete_index(self) -> None:
        """Delete the search index.  Silently succeeds if it does not exist."""
        try:
            self._index_client.delete_index(self._index_name)
            logger.info("index_deleted", extra={"index": self._index_name})
        except ResourceNotFoundError:
            logger.info("index_delete_skipped_not_found", extra={"index": self._index_name})

    def index_exists(self) -> bool:
        try:
            self._index_client.get_index(self._index_name)
            return True
        except ResourceNotFoundError:
            return False

    def get_index_stats(self) -> IndexStats:
        """Return document count and storage size for the index."""
        try:
            stats = self._index_client.get_index_statistics(self._index_name)
            return IndexStats(
                document_count=stats.get("document_count", 0),
                storage_size_bytes=stats.get("storage_size", 0),
            )
        except ResourceNotFoundError:
            return IndexStats(document_count=0, storage_size_bytes=0)

    # ── document operations ───────────────────────────────────

    def upload_documents(self, documents: list[dict[str, Any]]) -> int:
        """Upload or merge documents into the index.  Returns uploaded count."""
        if not documents:
            return 0
        result = self._search_client.upload_documents(documents=documents)
        succeeded = sum(1 for r in result if r.succeeded)
        failed = len(result) - succeeded
        if failed:
            logger.warning(
                "upload_partial_failure",
                extra={"succeeded": succeeded, "failed": failed},
            )
        return succeeded

    def delete_documents_by_doc_id(self, doc_id: str) -> int:
        """Delete every document whose doc_id matches (via filter + key lookup)."""
        keys_to_delete: list[str] = []
        results = self._search_client.search(
            search_text="*",
            filter=f"doc_id eq '{doc_id}'",
            select=["chunk_id"],
        )
        for result in results:
            keys_to_delete.append(result["chunk_id"])

        if not keys_to_delete:
            return 0

        batch = [{"chunk_id": key} for key in keys_to_delete]
        delete_result = self._search_client.delete_documents(documents=batch)
        deleted = sum(1 for r in delete_result if r.succeeded)
        logger.info(
            "documents_deleted",
            extra={"doc_id": doc_id, "deleted": deleted},
        )
        return deleted

    # ── search ────────────────────────────────────────────────

    def search(
        self,
        query: str,
        *,
        top: int = 5,
        select: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Execute a BM25 keyword search and return raw result dicts."""
        if select is None:
            select = [
                "chunk_id", "doc_id", "title", "section",
                "content", "url", "tags", "pipeline_version",
            ]
        results = self._search_client.search(
            search_text=query,
            top=top,
            select=select,
            include_total_count=False,
        )
        hits: list[dict[str, Any]] = []
        for result in results:
            hit = {field: result.get(field) for field in select}
            hit["score"] = result.get("@search.score", 0.0)
            hits.append(hit)
        return hits

    # ── health ────────────────────────────────────────────────

    def ping(self) -> bool:
        """Quick connectivity check against the index service."""
        try:
            self._index_client.get_service_statistics()
            return True
        except Exception:
            return False
