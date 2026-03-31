"""Unit tests for the ConfluenceParseService."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from kms_bot.services.parser import ConfluenceParseService


# ── fixtures ──────────────────────────────────────────────────


@pytest.fixture()
def _settings(tmp_path: Path):
    """Build a minimal ApplicationSettings pointing at temp directories."""
    from kms_bot.core.settings import ApplicationSettings

    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    cleaned_dir = tmp_path / "cleaned"
    cleaned_dir.mkdir()

    settings = ApplicationSettings(
        storage={
            "data_root": str(tmp_path),
            "raw_dir": str(raw_dir),
            "cleaned_dir": str(cleaned_dir),
            "chunks_dir": str(tmp_path / "chunks"),
            "sqlite_dir": str(tmp_path / "sqlite"),
            "logs_dir": str(tmp_path / "logs"),
        },
        database={"url": "sqlite:///:memory:"},
    )
    settings.bind_runtime_paths(repo_root=tmp_path, config_file_path=tmp_path / "app.yaml")
    return settings


@pytest.fixture()
def service(_settings) -> ConfluenceParseService:
    return ConfluenceParseService(_settings)


def _write_raw_artifact(raw_dir: Path, page_id: str, title: str, body_html: str) -> None:
    """Write a raw HTML + meta.json pair matching sync module's output contract."""
    (raw_dir / f"{page_id}.html").write_text(body_html, encoding="utf-8")
    meta = {
        "page_id": page_id,
        "title": title,
        "source_version": 1,
        "last_updated": "2025-01-01T00:00:00Z",
        "url": f"https://wiki.example.com/pages/{page_id}",
        "raw_hash": "abc123",
        "sync_time": "2025-01-01T00:00:00Z",
        "pipeline_version": 1,
    }
    (raw_dir / f"{page_id}.meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )


# ── parse_document tests ─────────────────────────────────────


class TestParseDocument:
    @pytest.mark.asyncio
    async def test_basic_parsing(self, service: ConfluenceParseService) -> None:
        html = "<h2>Overview</h2><p>Hello world.</p>"
        doc = await service.parse_document(
            doc_id="100", title="Test Page", raw_content=html
        )
        assert doc.doc_id == "100"
        assert doc.title == "Test Page"
        assert len(doc.sections) == 1
        assert doc.sections[0].heading == "Overview"
        assert "Hello world." in doc.sections[0].content
        assert doc.plain_text

    @pytest.mark.asyncio
    async def test_empty_html_produces_fallback(
        self, service: ConfluenceParseService
    ) -> None:
        doc = await service.parse_document(
            doc_id="101", title="Empty", raw_content=""
        )
        assert doc.doc_id == "101"
        assert len(doc.sections) >= 1
        assert doc.plain_text == "(empty page)"

    @pytest.mark.asyncio
    async def test_cleaned_document_validates_against_schema(
        self, service: ConfluenceParseService
    ) -> None:
        html = "<h2>Title</h2><p>Content here</p>"
        doc = await service.parse_document(
            doc_id="102", title="Schema Test", raw_content=html
        )
        # Should serialise and deserialise without error
        roundtripped = json.loads(doc.model_dump_json())
        assert roundtripped["doc_id"] == "102"
        assert isinstance(roundtripped["sections"], list)
        assert isinstance(roundtripped["plain_text"], str)


# ── parse_all tests ───────────────────────────────────────────


class TestParseAll:
    @pytest.mark.asyncio
    async def test_parse_all_processes_raw_artifacts(
        self, service: ConfluenceParseService, _settings
    ) -> None:
        raw_dir = _settings.resolve_path(_settings.storage.raw_dir)
        _write_raw_artifact(raw_dir, "200", "Page A", "<h2>A</h2><p>Alpha</p>")
        _write_raw_artifact(raw_dir, "201", "Page B", "<h2>B</h2><p>Beta</p>")

        docs = await service.parse_all()
        assert len(docs) == 2
        doc_ids = {d.doc_id for d in docs}
        assert doc_ids == {"200", "201"}

    @pytest.mark.asyncio
    async def test_parse_all_persists_cleaned_json(
        self, service: ConfluenceParseService, _settings
    ) -> None:
        raw_dir = _settings.resolve_path(_settings.storage.raw_dir)
        cleaned_dir = _settings.resolve_path(_settings.storage.cleaned_dir)
        _write_raw_artifact(raw_dir, "300", "Persist Test", "<h2>X</h2><p>Y</p>")

        await service.parse_all()

        output_file = cleaned_dir / "300.json"
        assert output_file.exists()
        data = json.loads(output_file.read_text(encoding="utf-8"))
        assert data["doc_id"] == "300"
        assert data["title"] == "Persist Test"

    @pytest.mark.asyncio
    async def test_parse_all_empty_directory(
        self, service: ConfluenceParseService
    ) -> None:
        docs = await service.parse_all()
        assert docs == []

    @pytest.mark.asyncio
    async def test_parse_all_skips_broken_artifact(
        self, service: ConfluenceParseService, _settings
    ) -> None:
        raw_dir = _settings.resolve_path(_settings.storage.raw_dir)
        _write_raw_artifact(raw_dir, "400", "Good Page", "<h2>OK</h2><p>Fine</p>")

        # Write a broken meta file (missing required fields)
        (raw_dir / "401.meta.json").write_text("{}", encoding="utf-8")
        (raw_dir / "401.html").write_text("<p>broken</p>", encoding="utf-8")

        docs = await service.parse_all()
        # Should still get the good one
        assert len(docs) == 1
        assert docs[0].doc_id == "400"
