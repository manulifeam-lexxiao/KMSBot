"""Chunker / Normalizer – converts cleaned documents into search-ready chunks."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from kms_bot.core.settings import ApplicationSettings
from kms_bot.repositories.document_registry import DocumentRegistryRepository
from kms_bot.schemas.documents import ChunkRecord, CleanedDocument, CleanedSection
from kms_bot.services.interfaces import ChunkService

logger = logging.getLogger(__name__)

MAX_CHUNK_CHARS = 1500
"""Soft ceiling for chunk content length (characters)."""

_STOP_WORDS: frozenset[str] = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "from",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "can",
        "shall",
        "this",
        "that",
        "these",
        "those",
        "it",
        "its",
        "how",
        "what",
        "when",
        "where",
        "who",
        "which",
        "not",
        "no",
        "if",
        "then",
        "so",
        "as",
        "up",
        "about",
    }
)


# ── pure helpers (no IO) ─────────────────────────────────────


def _slugify(text: str, *, max_length: int = 40) -> str:
    """Convert heading text to a slug matching ``[a-z0-9_-]+``."""
    slug = text.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    if not slug:
        slug = "content"
    return slug[:max_length].rstrip("-")


def _extract_tags(title: str, section_heading: str) -> list[str]:
    """Return deterministic, sorted tags from title and section heading."""
    combined = f"{title} {section_heading}".lower()
    words = re.findall(r"[a-z0-9]+", combined)
    return sorted(set(w for w in words if w not in _STOP_WORDS and len(w) > 1))


def _hard_split(content: str, *, max_size: int) -> list[str]:
    """Split *content* at word boundaries, hard-limit at *max_size*."""
    chunks: list[str] = []
    while content:
        if len(content) <= max_size:
            chunks.append(content)
            break
        split_at = content.rfind(" ", 0, max_size)
        if split_at <= 0:
            split_at = max_size  # no word boundary found – force split
        chunks.append(content[:split_at].rstrip())
        content = content[split_at:].lstrip()
    return chunks


def _greedy_merge(parts: list[str], *, max_size: int, separator: str) -> list[str]:
    """Greedily merge *parts* into chunks that stay under *max_size*."""
    chunks: list[str] = []
    current = ""
    sep_len = len(separator)

    for part in parts:
        part = part.strip()
        if not part:
            continue
        if not current:
            current = part
        elif len(current) + sep_len + len(part) <= max_size:
            current = current + separator + part
        else:
            chunks.append(current)
            current = part
    if current:
        chunks.append(current)

    # Any individual chunk still over max_size gets hard-split
    result: list[str] = []
    for chunk in chunks:
        if len(chunk) <= max_size:
            result.append(chunk)
        else:
            result.extend(_hard_split(chunk, max_size=max_size))
    return result


def _split_section(content: str, *, max_size: int = MAX_CHUNK_CHARS) -> list[str]:
    """Split section content into <= *max_size* character pieces.

    Strategy order:
    1. fits already → return as-is
    2. paragraph boundaries (``\\n\\n``)
    3. sentence boundaries (``. `` / ``! `` / ``? ``)
    4. word-boundary hard split
    """
    content = content.strip()
    if not content:
        return []
    if len(content) <= max_size:
        return [content]

    # 1. paragraph split
    paragraphs = re.split(r"\n\s*\n", content)
    if len(paragraphs) > 1:
        return _greedy_merge(paragraphs, max_size=max_size, separator="\n\n")

    # 2. sentence split
    sentences = re.split(r"(?<=[.!?])\s+", content)
    if len(sentences) > 1:
        return _greedy_merge(sentences, max_size=max_size, separator=" ")

    # 3. hard split
    return _hard_split(content, max_size=max_size)


def _build_chunks_for_section(
    *,
    doc_id: str,
    title: str,
    section: CleanedSection,
    url: str,
    pipeline_version: int,
) -> list[ChunkRecord]:
    """Produce one or more ``ChunkRecord`` instances for a single section."""
    parts = _split_section(section.content)
    if not parts:
        return []

    slug = _slugify(section.heading)
    tags = _extract_tags(title, section.heading)

    return [
        ChunkRecord(
            chunk_id=f"{doc_id}#{slug}#{idx}",
            doc_id=doc_id,
            title=title,
            section=section.heading,
            content=part,
            url=url,
            tags=tags,
            pipeline_version=pipeline_version,
        )
        for idx, part in enumerate(parts, start=1)
    ]


# ── service ───────────────────────────────────────────────────


class ConfluenceChunkService(ChunkService):
    """Heading-first chunker that reads cleaned JSON and emits chunk artifacts."""

    def __init__(
        self,
        settings: ApplicationSettings,
        registry_repository: DocumentRegistryRepository,
    ) -> None:
        self._settings = settings
        self._pipeline_version: int = settings.app.pipeline_version
        self._raw_dir: Path = settings.resolve_path(settings.storage.raw_dir)
        self._cleaned_dir: Path = settings.resolve_path(settings.storage.cleaned_dir)
        self._chunks_dir: Path = settings.resolve_path(settings.storage.chunks_dir)
        self._registry = registry_repository

    # ── ChunkService interface ────────────────────────────────

    async def chunk_document(self, document: CleanedDocument, *, url: str) -> list[ChunkRecord]:
        """Chunk a single cleaned document into ``ChunkRecord`` instances."""
        chunks: list[ChunkRecord] = []
        for section in document.sections:
            section_chunks = _build_chunks_for_section(
                doc_id=document.doc_id,
                title=document.title,
                section=section,
                url=url,
                pipeline_version=self._pipeline_version,
            )
            chunks.extend(section_chunks)
        return chunks

    # ── batch processing ──────────────────────────────────────

    async def chunk_all(self) -> list[ChunkRecord]:
        """Chunk every cleaned document and persist chunk artifacts.

        Returns the flat list of all produced chunks.
        """
        self._chunks_dir.mkdir(parents=True, exist_ok=True)

        all_chunks: list[ChunkRecord] = []
        cleaned_files = sorted(self._cleaned_dir.glob("*.json"))

        if not cleaned_files:
            logger.info(
                "no_cleaned_documents_found",
                extra={"cleaned_dir": str(self._cleaned_dir)},
            )
            return all_chunks

        for cleaned_path in cleaned_files:
            try:
                doc = CleanedDocument.model_validate_json(cleaned_path.read_text(encoding="utf-8"))
                url = self._resolve_url(doc.doc_id)
                chunks = await self.chunk_document(doc, url=url)
                self._persist_chunks(doc.doc_id, chunks)
                self._update_registry(doc.doc_id, len(chunks))
                all_chunks.extend(chunks)
                logger.info(
                    "document_chunked",
                    extra={"doc_id": doc.doc_id, "chunk_count": len(chunks)},
                )
            except Exception as exc:
                logger.warning(
                    "document_chunk_error",
                    extra={"file": str(cleaned_path), "error": str(exc)},
                )

        logger.info("chunk_all_completed", extra={"total_chunks": len(all_chunks)})
        return all_chunks

    # ── internal helpers ──────────────────────────────────────

    def _resolve_url(self, doc_id: str) -> str:
        """Read the page URL from the raw metadata sidecar."""
        meta_path = self._raw_dir / f"{doc_id}.meta.json"
        if meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            url = meta.get("url")
            if url:
                return str(url)
        logger.debug(
            "url_fallback_used",
            extra={"doc_id": doc_id},
        )
        return f"https://wiki.example.com/pages/{doc_id}"

    def _persist_chunks(self, doc_id: str, chunks: list[ChunkRecord]) -> None:
        """Write chunk list as JSON to ``data/chunks/{doc_id}.chunks.json``."""
        self._chunks_dir.mkdir(parents=True, exist_ok=True)
        output_path = self._chunks_dir / f"{doc_id}.chunks.json"
        data = [chunk.model_dump(mode="json") for chunk in chunks]
        output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def _update_registry(self, doc_id: str, chunk_count: int) -> None:
        """Persist chunk_count into the document registry."""
        self._registry.update_chunk_count(page_id=doc_id, chunk_count=chunk_count)
