"""Unit tests for the Azure AI Search module.

These tests verify the AzureAISearchService without requiring a live
Azure AI Search endpoint.  The low-level AzureSearchClient is replaced
with an in-memory stub so the business logic can be exercised in
isolation.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from kms_bot.core.settings import ApplicationSettings
from kms_bot.schemas.documents import ChunkRecord
from kms_bot.schemas.query import SearchResultHit
from kms_bot.services.azure_search_client import AzureSearchClient, IndexStats
from kms_bot.services.search import AzureAISearchService


# ── fixtures ──────────────────────────────────────────────────


@pytest.fixture()
def settings(tmp_path: Path) -> ApplicationSettings:
    chunks_dir = tmp_path / "chunks"
    chunks_dir.mkdir()

    s = ApplicationSettings(
        storage={
            "data_root": str(tmp_path),
            "raw_dir": str(tmp_path / "raw"),
            "cleaned_dir": str(tmp_path / "cleaned"),
            "chunks_dir": str(chunks_dir),
            "sqlite_dir": str(tmp_path / "sqlite"),
            "logs_dir": str(tmp_path / "logs"),
        },
        database={"url": "sqlite:///:memory:"},
        app={"pipeline_version": 1},
        search={"endpoint": "https://test.search.windows.net", "api_key": "fake", "index_name": "test-idx"},
    )
    s.bind_runtime_paths(repo_root=tmp_path, config_file_path=tmp_path / "app.yaml")
    return s


class _StubRegistry:
    """In-memory registry stub for unit tests."""

    def __init__(self) -> None:
        self.updates: list[dict[str, Any]] = []

    def update_index_status(
        self, *, page_id: str, index_status: str, last_index_time: str | None = None
    ) -> None:
        self.updates.append(
            {"page_id": page_id, "index_status": index_status, "last_index_time": last_index_time}
        )


@pytest.fixture()
def registry() -> _StubRegistry:
    return _StubRegistry()


class _StubAzureClient:
    """In-memory substitute for AzureSearchClient."""

    def __init__(self) -> None:
        self.index_created = False
        self.index_deleted = False
        self.uploaded_docs: list[dict[str, Any]] = []
        self.deleted_doc_ids: list[str] = []
        self._documents: list[dict[str, Any]] = []

    def create_or_update_index(self) -> None:
        self.index_created = True

    def delete_index(self) -> None:
        self.index_deleted = True
        self._documents.clear()

    def index_exists(self) -> bool:
        return self.index_created

    def get_index_stats(self) -> IndexStats:
        return IndexStats(document_count=len(self._documents), storage_size_bytes=0)

    def upload_documents(self, documents: list[dict[str, Any]]) -> int:
        self.uploaded_docs.extend(documents)
        self._documents.extend(documents)
        return len(documents)

    def delete_documents_by_doc_id(self, doc_id: str) -> int:
        before = len(self._documents)
        self._documents = [d for d in self._documents if d.get("doc_id") != doc_id]
        deleted = before - len(self._documents)
        self.deleted_doc_ids.append(doc_id)
        return deleted

    def search(self, query: str, *, top: int = 5, select: list[str] | None = None) -> list[dict[str, Any]]:
        """Simple substring match for testing."""
        hits: list[dict[str, Any]] = []
        q = query.lower()
        for doc in self._documents:
            content = (doc.get("content", "") + " " + doc.get("title", "")).lower()
            if q in content or q == "*":
                hit = dict(doc)
                hit["score"] = 1.0
                hits.append(hit)
                if len(hits) >= top:
                    break
        return hits

    def ping(self) -> bool:
        return True


@pytest.fixture()
def azure_client() -> _StubAzureClient:
    return _StubAzureClient()


@pytest.fixture()
def service(
    settings: ApplicationSettings,
    azure_client: _StubAzureClient,
    registry: _StubRegistry,
) -> AzureAISearchService:
    return AzureAISearchService(
        settings=settings,
        azure_client=azure_client,  # type: ignore[arg-type]
        registry_repository=registry,  # type: ignore[arg-type]
    )


# ── sample data ───────────────────────────────────────────────

SAMPLE_CHUNKS = [
    ChunkRecord(
        chunk_id="100#overview#1",
        doc_id="100",
        title="How to reset iPension access",
        section="Overview",
        content="This guide explains how to reset iPension access for employees.",
        url="https://wiki.example.com/pages/100",
        tags=["ipension", "access", "reset"],
        pipeline_version=1,
    ),
    ChunkRecord(
        chunk_id="100#steps#1",
        doc_id="100",
        title="How to reset iPension access",
        section="Steps",
        content="Step 1: Open the portal. Step 2: Click reset.",
        url="https://wiki.example.com/pages/100",
        tags=["ipension", "access", "reset", "steps"],
        pipeline_version=1,
    ),
    ChunkRecord(
        chunk_id="200#overview#1",
        doc_id="200",
        title="VPN Setup Guide",
        section="Overview",
        content="How to configure VPN for remote access to the corporate network.",
        url="https://wiki.example.com/pages/200",
        tags=["vpn", "network", "remote"],
        pipeline_version=1,
    ),
]


def _write_chunks(chunks_dir: Path, doc_id: str, chunks: list[ChunkRecord]) -> None:
    data = [c.model_dump(mode="json") for c in chunks]
    (chunks_dir / f"{doc_id}.chunks.json").write_text(
        json.dumps(data, ensure_ascii=False), encoding="utf-8"
    )


# ── tests: search ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_returns_search_result_hits(
    service: AzureAISearchService, azure_client: _StubAzureClient
) -> None:
    # Seed the stub with documents
    azure_client._documents = [
        {
            "chunk_id": "100#overview#1",
            "doc_id": "100",
            "title": "How to reset iPension access",
            "section": "Overview",
            "content": "This guide explains how to reset iPension access.",
            "url": "https://wiki.example.com/pages/100",
            "tags": ["ipension"],
            "pipeline_version": 1,
        }
    ]
    results = await service.search(query="ipension", top_k=5)
    assert len(results) == 1
    hit = results[0]
    assert isinstance(hit, SearchResultHit)
    assert hit.chunk_id == "100#overview#1"
    assert hit.doc_id == "100"
    assert hit.score == 1.0


@pytest.mark.asyncio
async def test_search_empty_results(service: AzureAISearchService) -> None:
    results = await service.search(query="nonexistent", top_k=5)
    assert results == []


# ── tests: rebuild index ──────────────────────────────────────


@pytest.mark.asyncio
async def test_rebuild_index_loads_chunks_and_uploads(
    service: AzureAISearchService,
    azure_client: _StubAzureClient,
    registry: _StubRegistry,
    settings: ApplicationSettings,
) -> None:
    chunks_dir = settings.resolve_path(settings.storage.chunks_dir)
    _write_chunks(chunks_dir, "100", [c for c in SAMPLE_CHUNKS if c.doc_id == "100"])
    _write_chunks(chunks_dir, "200", [c for c in SAMPLE_CHUNKS if c.doc_id == "200"])

    response = await service.rebuild_index()
    assert response.status == "accepted"
    assert response.job_type == "index_rebuild"

    # Wait for the background task to finish
    import asyncio
    await asyncio.sleep(0.5)

    status = await service.get_index_status()
    assert status.status == "success"
    assert status.indexed_documents == 2
    assert status.indexed_chunks == 3

    # Azure client received all docs
    assert azure_client.index_deleted is True
    assert azure_client.index_created is True
    assert len(azure_client.uploaded_docs) == 3

    # Registry updated
    updated_ids = {u["page_id"] for u in registry.updates}
    assert updated_ids == {"100", "200"}
    for update in registry.updates:
        assert update["index_status"] == "indexed"


@pytest.mark.asyncio
async def test_rebuild_with_no_chunks(
    service: AzureAISearchService,
    azure_client: _StubAzureClient,
) -> None:
    response = await service.rebuild_index()
    assert response.status == "accepted"

    import asyncio
    await asyncio.sleep(0.5)

    status = await service.get_index_status()
    assert status.status == "success"
    assert status.indexed_chunks == 0
    assert status.indexed_documents == 0


# ── tests: index status ──────────────────────────────────────


@pytest.mark.asyncio
async def test_initial_index_status_is_idle(service: AzureAISearchService) -> None:
    status = await service.get_index_status()
    assert status.status == "idle"
    assert status.current_job_id is None
    assert status.indexed_chunks == 0


# ── tests: stub azure client ─────────────────────────────────


def test_stub_azure_client_delete_by_doc_id(azure_client: _StubAzureClient) -> None:
    azure_client._documents = [
        {"chunk_id": "a#1#1", "doc_id": "a"},
        {"chunk_id": "a#1#2", "doc_id": "a"},
        {"chunk_id": "b#1#1", "doc_id": "b"},
    ]
    deleted = azure_client.delete_documents_by_doc_id("a")
    assert deleted == 2
    assert len(azure_client._documents) == 1
    assert azure_client._documents[0]["doc_id"] == "b"


# ── tests: chunk_to_index_doc ────────────────────────────────


def test_chunk_to_index_doc_shape() -> None:
    chunk = SAMPLE_CHUNKS[0]
    doc = AzureAISearchService._chunk_to_index_doc(chunk)
    assert doc["chunk_id"] == chunk.chunk_id
    assert doc["doc_id"] == chunk.doc_id
    assert doc["title"] == chunk.title
    assert doc["section"] == chunk.section
    assert doc["content"] == chunk.content
    assert doc["tags"] == chunk.tags
    assert doc["url"] == str(chunk.url)
    assert doc["pipeline_version"] == chunk.pipeline_version
    assert "last_updated" in doc


# ── tests: to_search_result_hit ──────────────────────────────


def test_to_search_result_hit_conversion() -> None:
    raw = {
        "chunk_id": "100#overview#1",
        "doc_id": "100",
        "title": "Test",
        "section": "Overview",
        "content": "Some content",
        "url": "https://wiki.example.com/pages/100",
        "tags": ["test"],
        "pipeline_version": 1,
        "score": 0.85,
    }
    hit = AzureAISearchService._to_search_result_hit(raw)
    assert isinstance(hit, SearchResultHit)
    assert hit.score == 0.85
    assert hit.chunk_id == "100#overview#1"
