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

import logging
import re
from collections import Counter
from difflib import SequenceMatcher

from kms_bot.core.settings import ApplicationSettings
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

    Depends only on ``SearchService`` and ``AnswerService`` interfaces –
    no Azure SDK imports leak into this module.
    """

    def __init__(
        self,
        *,
        settings: ApplicationSettings,
        search_service: SearchService,
        answer_service: AnswerService,
    ) -> None:
        self._settings = settings
        self._search = search_service
        self._answer = answer_service

    async def answer_query(self, request: QueryRequest) -> QueryResponse:
        normalized = normalize_query(request.query)
        logger.info("Query received – normalized: %r  top_k: %d", normalized, request.top_k)

        # ---- search ----
        raw_hits = await self._search.search(query=normalized, top_k=request.top_k)
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
        logger.debug(
            "After dedup/cap: %d → %d → %d",
            len(raw_hits),
            len(deduped),
            len(selected),
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
