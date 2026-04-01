"""Query orchestration layer.

Accepts a user question, preprocesses it, calls the search provider,
selects and normalizes top results, assembles LLM-ready context, and
emits the final retrieval package for answer generation and UI
consumption.

Normalisation rules
-------------------
1. Strip leading / trailing whitespace
2. Collapse consecutive whitespace to a single space
3. Lowercase
4. Strip trailing sentence-ending punctuation (? ! .)

Near-duplicate suppression
--------------------------
Two chunks are considered near-duplicates when the ``SequenceMatcher``
ratio of their lowercased content exceeds the configured
``similarity_threshold`` (default 0.85).  The second chunk is dropped.

Same-document cap
-----------------
At most ``max_chunks_per_doc`` chunks from any single ``doc_id`` are
kept; extras are dropped in order of descending score.

Context text format (LLM input)
-------------------------------
::

    --- Chunk 1 ---
    Document: <title>
    Section: <section>
    Chunk ID: <chunk_id>

    <content>

    --- Chunk 2 ---
    ...
"""

from __future__ import annotations

import json
import logging
import re
from collections import Counter
from collections.abc import AsyncIterator
from difflib import SequenceMatcher

from kms_bot.core.settings import ApplicationSettings
from kms_bot.repositories.document_registry import DocumentRegistryRepository
from kms_bot.schemas.query import (
    AnswerGeneratorInput,
    QueryDebugInfo,
    QueryRequest,
    QueryResponse,
    QuerySource,
    RelatedDocument,
    SearchResultHit,
)
from kms_bot.services.interfaces import AnswerService, QueryService, SearchService
from kms_bot.services.query_planner import QueryPlan, QueryPlannerService
from kms_bot.services.title_search import TitleSearchService

logger = logging.getLogger(__name__)

_TRAILING_PUNCT = re.compile(r"[?.!]+$")
_WHITESPACE = re.compile(r"\s+")


def normalize_query(raw: str) -> str:
    """Apply deterministic normalization to a user query string."""
    text = raw.strip()
    text = _WHITESPACE.sub(" ", text)
    text = text.lower()
    text = _TRAILING_PUNCT.sub("", text).rstrip()
    return text


def _content_key(content: str) -> str:
    """Lowercase + collapse whitespace for comparison purposes."""
    return _WHITESPACE.sub(" ", content.strip().lower())


def _is_near_duplicate(a: str, b: str, threshold: float) -> bool:
    """Return True when two content strings are near-duplicates."""
    if a == b:
        return True
    return SequenceMatcher(None, a, b).ratio() >= threshold


def suppress_duplicates(
    hits: list[SearchResultHit],
    *,
    similarity_threshold: float,
) -> list[SearchResultHit]:
    """Drop exact and near-duplicate chunks (by content)."""
    kept: list[SearchResultHit] = []
    kept_keys: list[str] = []
    for hit in hits:
        key = _content_key(hit.content)
        if any(_is_near_duplicate(key, k, similarity_threshold) for k in kept_keys):
            logger.debug("Dropping near-duplicate chunk %s", hit.chunk_id)
            continue
        kept.append(hit)
        kept_keys.append(key)
    return kept


def cap_per_document(
    hits: list[SearchResultHit],
    *,
    max_per_doc: int,
) -> list[SearchResultHit]:
    """Keep at most *max_per_doc* chunks from any single document."""
    counts: Counter[str] = Counter()
    kept: list[SearchResultHit] = []
    for hit in hits:
        if counts[hit.doc_id] >= max_per_doc:
            logger.debug(
                "Dropping chunk %s – doc %s already has %d chunks",
                hit.chunk_id,
                hit.doc_id,
                max_per_doc,
            )
            continue
        counts[hit.doc_id] += 1
        kept.append(hit)
    return kept


def assemble_context(chunks: list[SearchResultHit]) -> str:
    """Build the LLM-ready context text block from selected chunks."""
    parts: list[str] = []
    for idx, chunk in enumerate(chunks, start=1):
        part = (
            f"--- Chunk {idx} ---\n"
            f"Document: {chunk.title}\n"
            f"Section: {chunk.section}\n"
            f"Chunk ID: {chunk.chunk_id}\n"
            f"\n{chunk.content}"
        )
        parts.append(part)
    return "\n\n".join(parts)


def build_sources(chunks: list[SearchResultHit]) -> list[QuerySource]:
    """Convert selected chunks to UI source objects."""
    return [
        QuerySource(
            title=c.title,
            url=c.url,
            section=c.section,
            doc_id=c.doc_id,
            chunk_id=c.chunk_id,
        )
        for c in chunks
    ]


def extract_related_documents(chunks: list[SearchResultHit]) -> list[RelatedDocument]:
    """Unique related documents in order of first appearance."""
    seen: dict[str, RelatedDocument] = {}
    for c in chunks:
        seen.setdefault(
            c.doc_id,
            RelatedDocument(page_id=c.doc_id, title=c.title, url=c.url),
        )
    return list(seen.values())


class QueryOrchestratorService(QueryService):
    """Production implementation of the query orchestration layer.

    Supports two modes:
    - Standard: AI planning → title search → return relevant articles
    - THINKING: AI planning → title search → deep read → AI summary (via SSE)
    """

    def __init__(
        self,
        *,
        settings: ApplicationSettings,
        search_service: SearchService,
        answer_service: AnswerService,
        query_planner: QueryPlannerService | None = None,
        title_search: TitleSearchService | None = None,
        registry_repository: DocumentRegistryRepository | None = None,
    ) -> None:
        self._settings = settings
        self._search = search_service
        self._answer = answer_service
        self._planner = query_planner
        self._title_search = title_search
        self._registry = registry_repository

    async def answer_query(self, request: QueryRequest) -> QueryResponse:
        normalized = normalize_query(request.query)
        mode = "thinking" if request.thinking else "standard"
        logger.info(
            "Query received – normalized: %r  top_k: %d  mode: %s", normalized, request.top_k, mode
        )

        # ---- AI 查询规划 ----
        plan: QueryPlan | None = None
        if self._planner:
            plan = await self._planner.plan(request.query, mode=mode)
            logger.info("Query plan: %s", plan)
            search_query = " ".join(plan.all_search_terms) if plan.all_search_terms else normalized
        else:
            search_query = normalized

        if request.thinking and self._title_search:
            return await self._thinking_mode(request, normalized, search_query, plan)

        # ---- 根据 query_type 路由 ----
        query_type = plan.query_type if plan else "knowledge_search"
        if query_type == "meta_query":
            return await self._meta_query_mode(request, normalized, plan)
        if query_type == "general_chat":
            return await self._general_chat_mode(request, normalized, plan)

        return await self._standard_mode(request, normalized, search_query, plan)

    async def _standard_mode(
        self,
        request: QueryRequest,
        normalized: str,
        search_query: str,
        plan: QueryPlan | None,
    ) -> QueryResponse:
        """标准模式：FTS 搜索 chunks → AI 生成答案。"""
        # ---- search ----
        raw_hits = await self._search.search(query=search_query, top_k=request.top_k)
        logger.debug("Search returned %d raw hits", len(raw_hits))

        # ---- post-processing pipeline ----
        deduped = suppress_duplicates(
            raw_hits,
            similarity_threshold=self._settings.query.similarity_threshold,
        )
        selected = cap_per_document(
            deduped,
            max_per_doc=self._settings.query.max_chunks_per_doc,
        )

        # ---- context assembly ----
        context_text = assemble_context(selected)

        # ---- answer generation ----
        payload = AnswerGeneratorInput(
            query=request.query,
            normalized_query=normalized,
            prompt_template_path=self._settings.prompts.query_answering,
            selected_chunks=selected,
            context_text=context_text,
            include_debug=request.include_debug,
        )
        answer = await self._answer.generate_answer(payload)

        # ---- response assembly ----
        debug = QueryDebugInfo(
            normalized_query=normalized,
            selected_chunks=selected if request.include_debug else [],
        )
        return QueryResponse(
            answer=answer,
            sources=build_sources(selected),
            related_documents=extract_related_documents(selected),
            debug=debug,
        )

    async def _meta_query_mode(
        self,
        request: QueryRequest,
        normalized: str,
        plan: QueryPlan | None,
    ) -> QueryResponse:
        """元查询模式：回答关于知识库本身的问题（文档列表、统计等）。"""
        logger.info("Routing to meta_query mode")

        if self._registry:
            stats = self._registry.get_summary_stats()
            context_parts = [
                f"Total documents: {stats['total_documents']}",
                f"Total content chunks: {stats['total_chunks']}",
            ]
            if stats["label_distribution"]:
                labels_text = ", ".join(
                    f"{label} ({count} docs)"
                    for label, count in stats["label_distribution"].items()
                )
                context_parts.append(f"Categories/Labels: {labels_text}")
            if stats["titles"]:
                max_titles = 30
                shown = stats["titles"][:max_titles]
                titles_text = "\n".join(f"- {t}" for t in shown)
                if len(stats["titles"]) > max_titles:
                    titles_text += f"\n  ... and {len(stats['titles']) - max_titles} more documents"
                context_parts.append(f"Sample document titles:\n{titles_text}")
            context_text = "\n\n".join(context_parts)
        else:
            context_text = "暂无知识库元数据可用。"

        payload = AnswerGeneratorInput(
            query=request.query,
            normalized_query=normalized,
            prompt_template_path="prompts/query_answering/meta_query.md",
            selected_chunks=[],
            context_text=context_text,
            include_debug=request.include_debug,
        )
        answer = await self._answer.generate_answer(payload)

        debug = QueryDebugInfo(
            normalized_query=normalized,
            selected_chunks=[],
            query_type="meta_query",
        )
        return QueryResponse(
            answer=answer,
            sources=[],
            related_documents=[],
            debug=debug,
        )

    async def _general_chat_mode(
        self,
        request: QueryRequest,
        normalized: str,
        plan: QueryPlan | None,
    ) -> QueryResponse:
        """通用对话模式：处理闲聊、问候等非知识库查询。"""
        logger.info("Routing to general_chat mode")

        payload = AnswerGeneratorInput(
            query=request.query,
            normalized_query=normalized,
            prompt_template_path="prompts/query_answering/general_chat.md",
            selected_chunks=[],
            context_text=request.query,
            include_debug=request.include_debug,
        )
        answer = await self._answer.generate_answer(payload)

        debug = QueryDebugInfo(
            normalized_query=normalized,
            selected_chunks=[],
            query_type="general_chat",
        )
        return QueryResponse(
            answer=answer,
            sources=[],
            related_documents=[],
            debug=debug,
        )

    async def _thinking_mode(
        self,
        request: QueryRequest,
        normalized: str,
        search_query: str,
        plan: QueryPlan | None,
    ) -> QueryResponse:
        """THINKING 深度模式：标题搜索 → 加载全文 → AI 深度分析。"""
        assert self._title_search is not None

        max_articles = self._settings.query.thinking_max_articles

        # 1. 标题搜索找到候选文章
        title_hits = await self._title_search.search(query=search_query, top_k=max_articles * 3)
        logger.info("THINKING: found %d candidate articles", len(title_hits))

        # 2. 取 top N 篇文章的全文 chunks（标题搜索无结果时 fallback 到 chunk FTS）
        selected_page_ids = [h.page_id for h in title_hits[:max_articles]]
        if not selected_page_ids:
            logger.info("THINKING: title search returned 0, falling back to chunk FTS")
            fallback_hits = await self._search.search(
                query=search_query, top_k=self._settings.query.top_k
            )
            seen_ids: dict[str, None] = {}
            for h in fallback_hits:
                seen_ids.setdefault(h.doc_id, None)
                if len(seen_ids) >= max_articles:
                    break
            selected_page_ids = list(seen_ids.keys())
        all_chunks = await self._load_chunks_for_pages(selected_page_ids)
        logger.info(
            "THINKING: loaded %d chunks from %d articles", len(all_chunks), len(selected_page_ids)
        )

        # 3. 构建 SearchResultHit 列表
        selected: list[SearchResultHit] = []
        for chunk in all_chunks:
            selected.append(
                SearchResultHit(
                    chunk_id=chunk.chunk_id,
                    doc_id=chunk.doc_id,
                    title=chunk.title,
                    section=chunk.section,
                    content=chunk.content,
                    url=chunk.url,
                    tags=chunk.tags,
                    pipeline_version=chunk.pipeline_version,
                    labels=chunk.labels,
                    score=1.0,
                )
            )

        # 4. 组装 context 并生成深度答案
        context_text = assemble_context(selected)

        payload = AnswerGeneratorInput(
            query=request.query,
            normalized_query=normalized,
            prompt_template_path=self._settings.prompts.query_answering,
            selected_chunks=selected,
            context_text=context_text,
            include_debug=request.include_debug,
        )
        answer = await self._answer.generate_answer(payload)

        debug = QueryDebugInfo(
            normalized_query=normalized,
            selected_chunks=selected if request.include_debug else [],
        )
        return QueryResponse(
            answer=answer,
            sources=build_sources(selected),
            related_documents=extract_related_documents(selected),
            debug=debug,
        )

    async def _load_chunks_for_pages(self, page_ids: list[str]) -> list:
        """从磁盘加载指定 page_id 的所有 chunks。"""
        from kms_bot.schemas.documents import ChunkRecord

        chunks_dir = self._settings.resolve_path(self._settings.storage.chunks_dir)
        all_chunks: list[ChunkRecord] = []
        for page_id in page_ids:
            chunk_file = chunks_dir / f"{page_id}.chunks.json"
            if chunk_file.exists():
                try:
                    raw = json.loads(chunk_file.read_text(encoding="utf-8"))
                    for item in raw:
                        all_chunks.append(ChunkRecord.model_validate(item))
                except Exception as exc:
                    logger.warning("Failed to load chunks for %s: %s", page_id, exc)
        return all_chunks

    async def answer_query_streaming(self, request: QueryRequest) -> AsyncIterator[dict]:
        """THINKING 模式的 SSE 流式响应生成器。"""
        normalized = normalize_query(request.query)

        # Stage 1: Planning
        yield {"stage": "planning", "message": "正在分析问题..."}

        plan: QueryPlan | None = None
        if self._planner:
            plan = await self._planner.plan(request.query, mode="thinking")
            search_query = " ".join(plan.all_search_terms) if plan.all_search_terms else normalized
        else:
            search_query = normalized

        # Stage 2: Searching
        yield {"stage": "searching", "message": "正在搜索相关文章..."}

        max_articles = self._settings.query.thinking_max_articles
        if self._title_search:
            title_hits = await self._title_search.search(query=search_query, top_k=max_articles * 3)
        else:
            title_hits = []

        selected_page_ids = [h.page_id for h in title_hits[:max_articles]]
        articles_found = len(title_hits)
        reading_count = len(selected_page_ids)

        # 标题搜索无结果时：fallback 到 chunk FTS，从搜索结果推导文章列表
        use_chunk_fallback = reading_count == 0
        if use_chunk_fallback:
            logger.info(
                "THINKING streaming: title search found 0 articles, falling back to chunk FTS"
            )
            fallback_hits = await self._search.search(
                query=search_query, top_k=self._settings.query.top_k
            )
            seen_ids: dict[str, None] = {}
            for h in fallback_hits:
                seen_ids.setdefault(h.doc_id, None)
                if len(seen_ids) >= max_articles:
                    break
            selected_page_ids = list(seen_ids.keys())
            reading_count = len(selected_page_ids)
            articles_found = reading_count

        yield {
            "stage": "searching",
            "message": f"找到 {articles_found} 篇相关文章，将深度阅读 {reading_count} 篇",
            "articles_found": articles_found,
            "reading": reading_count,
        }

        # Stage 3: Reading
        from kms_bot.schemas.documents import ChunkRecord

        chunks_dir = self._settings.resolve_path(self._settings.storage.chunks_dir)
        all_chunks: list[ChunkRecord] = []
        for idx, page_id in enumerate(selected_page_ids, 1):
            yield {
                "stage": "reading",
                "message": f"正在阅读第 {idx}/{reading_count} 篇文章...",
                "current": idx,
                "total": reading_count,
            }
            chunk_file = chunks_dir / f"{page_id}.chunks.json"
            if chunk_file.exists():
                try:
                    raw = json.loads(chunk_file.read_text(encoding="utf-8"))
                    for item in raw:
                        all_chunks.append(ChunkRecord.model_validate(item))
                except Exception:
                    pass

        # Stage 4: Summarizing
        yield {"stage": "summarizing", "message": "正在生成总结..."}

        selected: list[SearchResultHit] = []
        for chunk in all_chunks:
            selected.append(
                SearchResultHit(
                    chunk_id=chunk.chunk_id,
                    doc_id=chunk.doc_id,
                    title=chunk.title,
                    section=chunk.section,
                    content=chunk.content,
                    url=chunk.url,
                    tags=chunk.tags,
                    pipeline_version=chunk.pipeline_version,
                    labels=chunk.labels,
                    score=1.0,
                )
            )

        context_text = assemble_context(selected)
        payload = AnswerGeneratorInput(
            query=request.query,
            normalized_query=normalized,
            prompt_template_path=self._settings.prompts.query_answering,
            selected_chunks=selected,
            context_text=context_text,
            include_debug=request.include_debug,
        )
        answer = await self._answer.generate_answer(payload)

        debug = QueryDebugInfo(
            normalized_query=normalized,
            selected_chunks=selected if request.include_debug else [],
        )
        response = QueryResponse(
            answer=answer,
            sources=build_sources(selected),
            related_documents=extract_related_documents(selected),
            debug=debug,
        )

        yield {"stage": "done", "data": response.model_dump(mode="json")}
