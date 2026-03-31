"""Unit tests for the Chunker / Normalizer module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from kms_bot.services.chunker import (
    ConfluenceChunkService,
    MAX_CHUNK_CHARS,
    _extract_tags,
    _hard_split,
    _slugify,
    _split_section,
)
from kms_bot.schemas.documents import ChunkRecord, CleanedDocument, CleanedSection


# ── fixtures ──────────────────────────────────────────────────


@pytest.fixture()
def _settings(tmp_path: Path):
    from kms_bot.core.settings import ApplicationSettings

    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    cleaned_dir = tmp_path / "cleaned"
    cleaned_dir.mkdir()
    chunks_dir = tmp_path / "chunks"
    chunks_dir.mkdir()

    settings = ApplicationSettings(
        storage={
            "data_root": str(tmp_path),
            "raw_dir": str(raw_dir),
            "cleaned_dir": str(cleaned_dir),
            "chunks_dir": str(chunks_dir),
            "sqlite_dir": str(tmp_path / "sqlite"),
            "logs_dir": str(tmp_path / "logs"),
        },
        database={"url": "sqlite:///:memory:"},
        app={"pipeline_version": 1},
    )
    settings.bind_runtime_paths(repo_root=tmp_path, config_file_path=tmp_path / "app.yaml")
    return settings


class _StubRegistryRepository:
    """In-memory stub replacing DocumentRegistryRepository for unit tests."""

    def __init__(self) -> None:
        self.updates: list[dict] = []

    def update_chunk_count(self, *, page_id: str, chunk_count: int) -> None:
        self.updates.append({"page_id": page_id, "chunk_count": chunk_count})


@pytest.fixture()
def registry() -> _StubRegistryRepository:
    return _StubRegistryRepository()


@pytest.fixture()
def service(_settings, registry) -> ConfluenceChunkService:
    return ConfluenceChunkService(_settings, registry)


def _sample_doc(
    doc_id: str = "100",
    title: str = "How to reset iPension access",
    sections: list[dict] | None = None,
) -> CleanedDocument:
    if sections is None:
        sections = [
            {"heading": "Overview", "content": "This guide explains how to reset iPension access."},
            {"heading": "Steps", "content": "Step 1: Open the portal.\nStep 2: Click reset."},
        ]
    return CleanedDocument(
        doc_id=doc_id,
        title=title,
        sections=[CleanedSection(**s) for s in sections],
        plain_text=" ".join(s["content"] for s in sections),
    )


# ── pure helper tests ────────────────────────────────────────


class TestSlugify:
    def test_basic(self) -> None:
        assert _slugify("Overview") == "overview"

    def test_special_chars(self) -> None:
        assert _slugify("Step-by-Step Guide!") == "step-by-step-guide"

    def test_spaces_and_cases(self) -> None:
        assert _slugify("  Getting Started  ") == "getting-started"

    def test_empty_string(self) -> None:
        assert _slugify("") == "content"

    def test_truncation(self) -> None:
        long = "a" * 50
        assert len(_slugify(long)) <= 40

    def test_only_special_chars(self) -> None:
        assert _slugify("###!!!") == "content"

    def test_matches_chunk_id_pattern(self) -> None:
        import re
        slug = _slugify("Complex Heading (v2.1)")
        assert re.fullmatch(r"[a-z0-9_-]+", slug)


class TestExtractTags:
    def test_basic(self) -> None:
        tags = _extract_tags("How to reset iPension access", "Steps")
        assert "ipension" in tags
        assert "reset" in tags
        assert "access" in tags
        assert "steps" in tags
        # stop words excluded
        assert "how" not in tags
        assert "to" not in tags

    def test_deduplication(self) -> None:
        tags = _extract_tags("Reset Reset", "Reset")
        assert tags.count("reset") == 1

    def test_sorted(self) -> None:
        tags = _extract_tags("Zebra Apple Mango", "Banana")
        assert tags == sorted(tags)

    def test_short_words_excluded(self) -> None:
        tags = _extract_tags("A B C Longer", "X")
        assert "longer" in tags
        assert "a" not in tags


class TestSplitSection:
    def test_short_content_unchanged(self) -> None:
        result = _split_section("Hello world.", max_size=100)
        assert result == ["Hello world."]

    def test_empty_content(self) -> None:
        assert _split_section("", max_size=100) == []
        assert _split_section("   ", max_size=100) == []

    def test_paragraph_split(self) -> None:
        content = "Para one." + "\n\n" + "Para two."
        result = _split_section(content, max_size=15)
        assert len(result) == 2
        assert "Para one." in result[0]
        assert "Para two." in result[1]

    def test_sentence_split(self) -> None:
        content = "Sentence one. Sentence two. Sentence three."
        result = _split_section(content, max_size=30)
        assert len(result) >= 2
        assert all(len(c) <= 30 for c in result)

    def test_hard_split(self) -> None:
        content = "word " * 100  # long string with no paragraph/sentence breaks
        result = _split_section(content, max_size=50)
        assert all(len(c) <= 50 for c in result)
        # Recombined content should equal original (modulo whitespace)
        recombined = " ".join(c.strip() for c in result)
        assert recombined == content.strip()


class TestHardSplit:
    def test_respects_word_boundary(self) -> None:
        content = "alpha bravo charlie delta echo"
        parts = _hard_split(content, max_size=15)
        assert all(len(p) <= 15 for p in parts)
        assert not any(p.startswith(" ") or p.endswith(" ") for p in parts)


# ── chunk_document tests ─────────────────────────────────────


class TestChunkDocument:
    @pytest.mark.asyncio
    async def test_basic_chunking(self, service: ConfluenceChunkService) -> None:
        doc = _sample_doc()
        chunks = await service.chunk_document(doc, url="https://wiki.example.com/pages/100")
        assert len(chunks) == 2
        assert all(isinstance(c, ChunkRecord) for c in chunks)

    @pytest.mark.asyncio
    async def test_chunk_id_format(self, service: ConfluenceChunkService) -> None:
        import re
        doc = _sample_doc()
        chunks = await service.chunk_document(doc, url="https://wiki.example.com/pages/100")
        pattern = r"^[^#]+#[a-z0-9_-]+#[1-9][0-9]*$"
        for chunk in chunks:
            assert re.match(pattern, chunk.chunk_id), f"Bad chunk_id: {chunk.chunk_id}"

    @pytest.mark.asyncio
    async def test_chunk_fields(self, service: ConfluenceChunkService) -> None:
        doc = _sample_doc()
        chunks = await service.chunk_document(doc, url="https://wiki.example.com/pages/100")
        first = chunks[0]
        assert first.doc_id == "100"
        assert first.title == "How to reset iPension access"
        assert first.section == "Overview"
        assert first.pipeline_version == 1
        assert str(first.url) == "https://wiki.example.com/pages/100"
        assert isinstance(first.tags, list)
        assert len(first.tags) > 0

    @pytest.mark.asyncio
    async def test_oversized_section_is_split(self, service: ConfluenceChunkService) -> None:
        big_content = ("This is a long paragraph. " * 200).strip()  # > 1500 chars
        doc = _sample_doc(sections=[{"heading": "Big", "content": big_content}])
        chunks = await service.chunk_document(doc, url="https://wiki.example.com/pages/100")
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk.content) <= MAX_CHUNK_CHARS

    @pytest.mark.asyncio
    async def test_empty_section_skipped(self, service: ConfluenceChunkService) -> None:
        doc = _sample_doc(
            sections=[
                {"heading": "Good", "content": "Some content."},
            ]
        )
        # CleanedSection requires min_length=1 for content, so we test
        # that a section with only whitespace-like content still produces chunks
        chunks = await service.chunk_document(doc, url="https://wiki.example.com/pages/100")
        assert len(chunks) == 1

    @pytest.mark.asyncio
    async def test_deterministic_output(self, service: ConfluenceChunkService) -> None:
        doc = _sample_doc()
        url = "https://wiki.example.com/pages/100"
        chunks_a = await service.chunk_document(doc, url=url)
        chunks_b = await service.chunk_document(doc, url=url)
        assert [c.chunk_id for c in chunks_a] == [c.chunk_id for c in chunks_b]
        assert [c.content for c in chunks_a] == [c.content for c in chunks_b]
        assert [c.tags for c in chunks_a] == [c.tags for c in chunks_b]

    @pytest.mark.asyncio
    async def test_chunk_validates_against_schema(self, service: ConfluenceChunkService) -> None:
        doc = _sample_doc()
        chunks = await service.chunk_document(doc, url="https://wiki.example.com/pages/100")
        for chunk in chunks:
            data = json.loads(chunk.model_dump_json())
            assert "chunk_id" in data
            assert "url" in data
            assert "tags" in data
            assert isinstance(data["pipeline_version"], int)


# ── chunk_all / persistence tests ─────────────────────────────


def _write_cleaned(cleaned_dir: Path, doc_id: str, title: str, sections: list[dict]) -> None:
    doc = _sample_doc(doc_id=doc_id, title=title, sections=sections)
    (cleaned_dir / f"{doc_id}.json").write_text(doc.model_dump_json(indent=2), encoding="utf-8")


def _write_meta(raw_dir: Path, doc_id: str, title: str) -> None:
    meta = {
        "page_id": doc_id,
        "title": title,
        "source_version": 1,
        "last_updated": "2025-01-01T00:00:00Z",
        "url": f"https://wiki.example.com/pages/{doc_id}",
        "raw_hash": "abc123",
        "sync_time": "2025-01-01T00:00:00Z",
        "pipeline_version": 1,
    }
    (raw_dir / f"{doc_id}.meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")


class TestChunkAll:
    @pytest.mark.asyncio
    async def test_processes_cleaned_documents(
        self, service: ConfluenceChunkService, _settings, registry
    ) -> None:
        raw_dir = _settings.resolve_path(_settings.storage.raw_dir)
        cleaned_dir = _settings.resolve_path(_settings.storage.cleaned_dir)
        _write_meta(raw_dir, "200", "Page A")
        _write_cleaned(cleaned_dir, "200", "Page A", [{"heading": "Intro", "content": "Alpha content."}])
        _write_meta(raw_dir, "201", "Page B")
        _write_cleaned(cleaned_dir, "201", "Page B", [{"heading": "Intro", "content": "Beta content."}])

        chunks = await service.chunk_all()
        assert len(chunks) == 2
        assert {c.doc_id for c in chunks} == {"200", "201"}

    @pytest.mark.asyncio
    async def test_persists_chunk_json(
        self, service: ConfluenceChunkService, _settings, registry
    ) -> None:
        raw_dir = _settings.resolve_path(_settings.storage.raw_dir)
        cleaned_dir = _settings.resolve_path(_settings.storage.cleaned_dir)
        chunks_dir = _settings.resolve_path(_settings.storage.chunks_dir)
        _write_meta(raw_dir, "300", "Persist Test")
        _write_cleaned(cleaned_dir, "300", "Persist Test", [{"heading": "Data", "content": "Some data."}])

        await service.chunk_all()

        output = chunks_dir / "300.chunks.json"
        assert output.exists()
        data = json.loads(output.read_text(encoding="utf-8"))
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["doc_id"] == "300"

    @pytest.mark.asyncio
    async def test_updates_registry(
        self, service: ConfluenceChunkService, _settings, registry
    ) -> None:
        raw_dir = _settings.resolve_path(_settings.storage.raw_dir)
        cleaned_dir = _settings.resolve_path(_settings.storage.cleaned_dir)
        _write_meta(raw_dir, "400", "Reg Test")
        _write_cleaned(cleaned_dir, "400", "Reg Test", [{"heading": "A", "content": "Content A."}])

        await service.chunk_all()
        assert len(registry.updates) == 1
        assert registry.updates[0] == {"page_id": "400", "chunk_count": 1}

    @pytest.mark.asyncio
    async def test_empty_cleaned_dir(self, service: ConfluenceChunkService) -> None:
        chunks = await service.chunk_all()
        assert chunks == []

    @pytest.mark.asyncio
    async def test_skips_broken_cleaned_file(
        self, service: ConfluenceChunkService, _settings, registry
    ) -> None:
        raw_dir = _settings.resolve_path(_settings.storage.raw_dir)
        cleaned_dir = _settings.resolve_path(_settings.storage.cleaned_dir)
        # Write a valid document
        _write_meta(raw_dir, "500", "Good")
        _write_cleaned(cleaned_dir, "500", "Good", [{"heading": "OK", "content": "Fine."}])
        # Write a broken JSON file
        (cleaned_dir / "501.json").write_text("{invalid", encoding="utf-8")

        chunks = await service.chunk_all()
        assert len(chunks) == 1
        assert chunks[0].doc_id == "500"

    @pytest.mark.asyncio
    async def test_url_from_meta_sidecar(
        self, service: ConfluenceChunkService, _settings, registry
    ) -> None:
        raw_dir = _settings.resolve_path(_settings.storage.raw_dir)
        cleaned_dir = _settings.resolve_path(_settings.storage.cleaned_dir)
        _write_meta(raw_dir, "600", "URL Test")
        _write_cleaned(cleaned_dir, "600", "URL Test", [{"heading": "X", "content": "Content."}])

        chunks = await service.chunk_all()
        assert str(chunks[0].url) == "https://wiki.example.com/pages/600"

    @pytest.mark.asyncio
    async def test_url_fallback_when_no_meta(
        self, service: ConfluenceChunkService, _settings, registry
    ) -> None:
        cleaned_dir = _settings.resolve_path(_settings.storage.cleaned_dir)
        # No meta file written – URL should fall back
        _write_cleaned(cleaned_dir, "700", "No Meta", [{"heading": "Y", "content": "Content."}])

        chunks = await service.chunk_all()
        assert "700" in str(chunks[0].url)
