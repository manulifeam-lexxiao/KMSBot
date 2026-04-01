"""Unit tests for the query orchestration layer.

These tests verify the QueryOrchestratorService without requiring
live Azure Search or OpenAI endpoints.  Stub implementations of the
SearchService and AnswerService interfaces are used throughout.
"""

from __future__ import annotations

import pytest

from kms_bot.core.settings import ApplicationSettings
from kms_bot.schemas.query import (
    AnswerGeneratorInput,
    QueryRequest,
    SearchResultHit,
)
from kms_bot.services.interfaces import AnswerService, SearchService
from kms_bot.services.query import (
    QueryOrchestratorService,
    assemble_context,
    build_sources,
    cap_per_document,
    extract_related_documents,
    normalize_query,
    suppress_duplicates,
)
from kms_bot.services.query_planner import QueryPlan, QueryPlannerService


# ── helpers ───────────────────────────────────────────────────


def _hit(
    chunk_id: str = "1#s#1",
    doc_id: str = "1",
    title: str = "Doc A",
    section: str = "Overview",
    content: str = "Some content",
    url: str = "https://example.com/1",
    score: float = 1.0,
    tags: list[str] | None = None,
    pipeline_version: int = 1,
) -> SearchResultHit:
    return SearchResultHit(
        chunk_id=chunk_id,
        doc_id=doc_id,
        title=title,
        section=section,
        content=content,
        url=url,
        score=score,
        tags=tags or [],
        pipeline_version=pipeline_version,
    )


class _StubSearchService(SearchService):
    def __init__(self, hits: list[SearchResultHit] | None = None) -> None:
        self._hits = hits or []

    async def search(self, *, query: str, top_k: int) -> list[SearchResultHit]:
        return self._hits[:top_k]

    async def rebuild_index(self):  # type: ignore[override]
        raise NotImplementedError

    async def get_index_status(self):  # type: ignore[override]
        raise NotImplementedError


class _StubAnswerService(AnswerService):
    def __init__(self, answer: str = "stub answer") -> None:
        self._answer = answer
        self.last_payload: AnswerGeneratorInput | None = None

    async def generate_answer(self, payload: AnswerGeneratorInput) -> str:
        self.last_payload = payload
        return self._answer


@pytest.fixture()
def settings() -> ApplicationSettings:
    s = ApplicationSettings(
        app={"pipeline_version": 1},
        query={"top_k": 5, "include_debug": False, "max_chunks_per_doc": 2, "similarity_threshold": 0.85},
    )
    return s


# ── normalize_query ───────────────────────────────────────────


class TestNormalizeQuery:
    def test_lowercase_and_strip(self) -> None:
        assert normalize_query("  Hello World  ") == "hello world"

    def test_collapse_whitespace(self) -> None:
        assert normalize_query("how   do  I   reset") == "how do i reset"

    def test_strip_trailing_punctuation(self) -> None:
        assert normalize_query("How to reset?") == "how to reset"
        assert normalize_query("What happened?!") == "what happened"

    def test_preserves_internal_punctuation(self) -> None:
        assert normalize_query("v2.1 config") == "v2.1 config"

    def test_empty_after_strip(self) -> None:
        assert normalize_query("???") == ""


# ── suppress_duplicates ──────────────────────────────────────


class TestSuppressDuplicates:
    def test_exact_duplicate_removed(self) -> None:
        hits = [
            _hit(chunk_id="a", content="Step 1 reset password"),
            _hit(chunk_id="b", content="Step 1 reset password"),
        ]
        result = suppress_duplicates(hits, similarity_threshold=0.85)
        assert len(result) == 1
        assert result[0].chunk_id == "a"

    def test_near_duplicate_removed(self) -> None:
        hits = [
            _hit(chunk_id="a", content="Step 1: reset your password immediately"),
            _hit(chunk_id="b", content="Step 1: reset your password immediately."),
        ]
        result = suppress_duplicates(hits, similarity_threshold=0.85)
        assert len(result) == 1

    def test_distinct_kept(self) -> None:
        hits = [
            _hit(chunk_id="a", content="Reset your password"),
            _hit(chunk_id="b", content="Configure VPN settings"),
        ]
        result = suppress_duplicates(hits, similarity_threshold=0.85)
        assert len(result) == 2


# ── cap_per_document ─────────────────────────────────────────


class TestCapPerDocument:
    def test_caps_at_limit(self) -> None:
        hits = [
            _hit(chunk_id="1#a#1", doc_id="1"),
            _hit(chunk_id="1#a#2", doc_id="1"),
            _hit(chunk_id="1#a#3", doc_id="1"),
        ]
        result = cap_per_document(hits, max_per_doc=2)
        assert len(result) == 2

    def test_different_docs_not_affected(self) -> None:
        hits = [
            _hit(chunk_id="1#a#1", doc_id="1"),
            _hit(chunk_id="2#a#1", doc_id="2"),
            _hit(chunk_id="1#a#2", doc_id="1"),
            _hit(chunk_id="2#a#2", doc_id="2"),
        ]
        result = cap_per_document(hits, max_per_doc=2)
        assert len(result) == 4


# ── assemble_context ─────────────────────────────────────────


class TestAssembleContext:
    def test_single_chunk(self) -> None:
        ctx = assemble_context([_hit(chunk_id="1#s#1", title="Doc A", section="Intro", content="Hello")])
        assert "--- Chunk 1 ---" in ctx
        assert "Document: Doc A" in ctx
        assert "Section: Intro" in ctx
        assert "Chunk ID: 1#s#1" in ctx
        assert "Hello" in ctx

    def test_multiple_chunks(self) -> None:
        ctx = assemble_context([
            _hit(chunk_id="a", content="First"),
            _hit(chunk_id="b", content="Second"),
        ])
        assert "--- Chunk 1 ---" in ctx
        assert "--- Chunk 2 ---" in ctx

    def test_empty(self) -> None:
        assert assemble_context([]) == ""


# ── build_sources ────────────────────────────────────────────


class TestBuildSources:
    def test_maps_fields(self) -> None:
        hit = _hit(chunk_id="x", doc_id="10", title="T", section="S", url="https://example.com/x")
        sources = build_sources([hit])
        assert len(sources) == 1
        assert sources[0].chunk_id == "x"
        assert sources[0].doc_id == "10"


# ── extract_related_documents ────────────────────────────────


class TestExtractRelatedDocuments:
    def test_deduplicates_by_doc_id(self) -> None:
        hits = [
            _hit(doc_id="1", title="D1", url="https://example.com/1"),
            _hit(doc_id="1", title="D1", url="https://example.com/1"),
            _hit(doc_id="2", title="D2", url="https://example.com/2"),
        ]
        related = extract_related_documents(hits)
        assert len(related) == 2
        assert related[0].page_id == "1"
        assert related[1].page_id == "2"


# ── QueryOrchestratorService (integration) ───────────────────


class TestQueryOrchestratorService:
    @pytest.mark.asyncio
    async def test_basic_flow(self, settings: ApplicationSettings) -> None:
        hits = [
            _hit(chunk_id="1#a#1", doc_id="1", content="Alpha"),
            _hit(chunk_id="2#a#1", doc_id="2", content="Beta"),
        ]
        search = _StubSearchService(hits)
        answer = _StubAnswerService("Generated answer")
        svc = QueryOrchestratorService(settings=settings, search_service=search, answer_service=answer)

        resp = await svc.answer_query(QueryRequest(query="test?", top_k=5, include_debug=True))

        assert resp.answer == "Generated answer"
        assert len(resp.sources) == 2
        assert len(resp.related_documents) == 2
        assert resp.debug.normalized_query == "test"
        assert len(resp.debug.selected_chunks) == 2

    @pytest.mark.asyncio
    async def test_debug_hidden_when_flag_false(self, settings: ApplicationSettings) -> None:
        hits = [_hit()]
        search = _StubSearchService(hits)
        answer = _StubAnswerService()
        svc = QueryOrchestratorService(settings=settings, search_service=search, answer_service=answer)

        resp = await svc.answer_query(QueryRequest(query="test", top_k=5, include_debug=False))
        assert resp.debug.selected_chunks == []

    @pytest.mark.asyncio
    async def test_duplicate_suppression_in_flow(self, settings: ApplicationSettings) -> None:
        hits = [
            _hit(chunk_id="a", content="Same content here"),
            _hit(chunk_id="b", content="Same content here"),
        ]
        search = _StubSearchService(hits)
        answer = _StubAnswerService()
        svc = QueryOrchestratorService(settings=settings, search_service=search, answer_service=answer)

        resp = await svc.answer_query(QueryRequest(query="test", top_k=5, include_debug=True))
        assert len(resp.sources) == 1

    @pytest.mark.asyncio
    async def test_per_doc_cap_in_flow(self, settings: ApplicationSettings) -> None:
        hits = [
            _hit(chunk_id="1#a#1", doc_id="1", content="A"),
            _hit(chunk_id="1#a#2", doc_id="1", content="B"),
            _hit(chunk_id="1#a#3", doc_id="1", content="C"),
        ]
        search = _StubSearchService(hits)
        answer = _StubAnswerService()
        svc = QueryOrchestratorService(settings=settings, search_service=search, answer_service=answer)

        resp = await svc.answer_query(QueryRequest(query="test", top_k=5, include_debug=True))
        # max_chunks_per_doc=2 in fixture
        assert len(resp.sources) == 2

    @pytest.mark.asyncio
    async def test_context_text_passed_to_answer_service(self, settings: ApplicationSettings) -> None:
        hits = [_hit(chunk_id="c1", content="Payload content")]
        search = _StubSearchService(hits)
        answer_svc = _StubAnswerService()
        svc = QueryOrchestratorService(settings=settings, search_service=search, answer_service=answer_svc)

        await svc.answer_query(QueryRequest(query="q", top_k=5, include_debug=False))

        assert answer_svc.last_payload is not None
        assert "Payload content" in answer_svc.last_payload.context_text

    @pytest.mark.asyncio
    async def test_empty_search_results(self, settings: ApplicationSettings) -> None:
        search = _StubSearchService([])
        answer = _StubAnswerService("No results")
        svc = QueryOrchestratorService(settings=settings, search_service=search, answer_service=answer)

        resp = await svc.answer_query(QueryRequest(query="unknown", top_k=5, include_debug=False))
        assert resp.answer == "No results"
        assert resp.sources == []
        assert resp.related_documents == []


# ── Stub QueryPlanner for routing tests ───────────────────────


class _StubQueryPlanner:
    """模拟 QueryPlannerService，返回指定 query_type 的 plan。"""

    def __init__(self, query_type: str = "knowledge_search") -> None:
        self._query_type = query_type

    async def plan(self, query: str, *, mode: str = "standard") -> QueryPlan:
        return QueryPlan(
            intent="find",
            search_keywords=[],
            label_filters=[],
            synonym_expansions=[],
            reasoning="stub",
            query_type=self._query_type,
        )


class _StubRegistryRepository:
    """模拟 DocumentRegistryRepository.get_summary_stats()。"""

    def get_summary_stats(self) -> dict:
        return {
            "total_documents": 3,
            "total_chunks": 15,
            "titles": ["Doc A", "Doc B", "Doc C"],
            "label_distribution": {"FAQ": 2, "Guide": 1},
        }


# ── Query routing tests ──────────────────────────────────────


class TestQueryRouting:
    @pytest.mark.asyncio
    async def test_meta_query_routing(self, settings: ApplicationSettings) -> None:
        search = _StubSearchService([])
        answer_svc = _StubAnswerService("知识库共有3篇文档")
        planner = _StubQueryPlanner(query_type="meta_query")
        registry = _StubRegistryRepository()

        svc = QueryOrchestratorService(
            settings=settings,
            search_service=search,
            answer_service=answer_svc,
            query_planner=planner,
            registry_repository=registry,
        )

        resp = await svc.answer_query(
            QueryRequest(query="数据库里有什么内容", top_k=5, include_debug=True)
        )
        assert resp.answer == "知识库共有3篇文档"
        assert resp.sources == []
        assert resp.debug.query_type == "meta_query"
        # 验证 meta_query 使用 meta_query.md 模板
        assert answer_svc.last_payload is not None
        assert "meta_query" in answer_svc.last_payload.prompt_template_path

    @pytest.mark.asyncio
    async def test_general_chat_routing(self, settings: ApplicationSettings) -> None:
        search = _StubSearchService([])
        answer_svc = _StubAnswerService("你好！我是 KMS Bot")
        planner = _StubQueryPlanner(query_type="general_chat")

        svc = QueryOrchestratorService(
            settings=settings,
            search_service=search,
            answer_service=answer_svc,
            query_planner=planner,
        )

        resp = await svc.answer_query(
            QueryRequest(query="你好", top_k=5, include_debug=True)
        )
        assert resp.answer == "你好！我是 KMS Bot"
        assert resp.sources == []
        assert resp.debug.query_type == "general_chat"
        # 验证 general_chat 使用 general_chat.md 模板
        assert answer_svc.last_payload is not None
        assert "general_chat" in answer_svc.last_payload.prompt_template_path

    @pytest.mark.asyncio
    async def test_knowledge_search_routing_unchanged(self, settings: ApplicationSettings) -> None:
        hits = [_hit(chunk_id="1#a#1", content="Alpha")]
        search = _StubSearchService(hits)
        answer_svc = _StubAnswerService("Answer from KB")
        planner = _StubQueryPlanner(query_type="knowledge_search")

        svc = QueryOrchestratorService(
            settings=settings,
            search_service=search,
            answer_service=answer_svc,
            query_planner=planner,
        )

        resp = await svc.answer_query(
            QueryRequest(query="how to reset password", top_k=5, include_debug=True)
        )
        assert resp.answer == "Answer from KB"
        assert len(resp.sources) == 1
        assert resp.debug.query_type == "knowledge_search"
