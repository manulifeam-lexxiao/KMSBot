"""Confluence HTML → CleanedDocument parser service."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from kms_bot.core.settings import ApplicationSettings
from kms_bot.schemas.documents import CleanedDocument, CleanedSection
from kms_bot.services.html_cleaner import clean_html
from kms_bot.services.interfaces import ParseService

logger = logging.getLogger(__name__)


class ConfluenceParseService(ParseService):
    """Parses raw Confluence HTML artifacts into cleaned structured JSON.

    Implements the ``ParseService`` interface for single-document parsing
    and adds a ``parse_all`` method for batch processing of raw artifacts.
    """

    def __init__(self, settings: ApplicationSettings) -> None:
        self._settings = settings
        self._raw_dir: Path = settings.resolve_path(settings.storage.raw_dir)
        self._cleaned_dir: Path = settings.resolve_path(settings.storage.cleaned_dir)

    # ── ParseService interface ────────────────────────────────

    async def parse_document(
        self, *, doc_id: str, title: str, raw_content: str
    ) -> CleanedDocument:
        """Parse a single document from raw HTML content."""
        sections, plain_text = clean_html(raw_content)

        cleaned_sections = [
            CleanedSection(heading=s.heading, content=s.content) for s in sections
        ]

        # Guarantee at least one section and non-empty plain_text
        if not cleaned_sections:
            cleaned_sections = [
                CleanedSection(
                    heading="Content", content=plain_text or "(empty page)"
                )
            ]

        if not plain_text:
            plain_text = "(empty page)"

        return CleanedDocument(
            doc_id=doc_id,
            title=title,
            sections=cleaned_sections,
            plain_text=plain_text,
        )

    # ── batch processing (independent of sync internals) ──────

    async def parse_all(self) -> list[CleanedDocument]:
        """Parse every raw artifact in the raw directory and persist cleaned JSON.

        Returns the list of successfully parsed documents.
        """
        self._cleaned_dir.mkdir(parents=True, exist_ok=True)

        results: list[CleanedDocument] = []
        meta_files = sorted(self._raw_dir.glob("*.meta.json"))

        if not meta_files:
            logger.info(
                "no_raw_artifacts_found", extra={"raw_dir": str(self._raw_dir)}
            )
            return results

        for meta_path in meta_files:
            try:
                doc = await self._parse_from_raw(meta_path)
                self._persist_cleaned(doc)
                results.append(doc)
                logger.info(
                    "document_parsed",
                    extra={"doc_id": doc.doc_id, "sections": len(doc.sections)},
                )
            except Exception as exc:
                logger.warning(
                    "document_parse_error",
                    extra={"meta_file": str(meta_path), "error": str(exc)},
                )

        logger.info("parse_all_completed", extra={"total": len(results)})
        return results

    # ── internal helpers ──────────────────────────────────────

    async def _parse_from_raw(self, meta_path: Path) -> CleanedDocument:
        """Load a raw artifact by its metadata sidecar and parse it."""
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        page_id = meta["page_id"]
        title = meta["title"]

        html_path = meta_path.parent / f"{page_id}.html"
        raw_html = html_path.read_text(encoding="utf-8")

        return await self.parse_document(
            doc_id=page_id, title=title, raw_content=raw_html
        )

    def _persist_cleaned(self, document: CleanedDocument) -> None:
        """Write cleaned document JSON to the cleaned directory."""
        self._cleaned_dir.mkdir(parents=True, exist_ok=True)
        output_path = self._cleaned_dir / f"{document.doc_id}.json"
        output_path.write_text(
            document.model_dump_json(indent=2),
            encoding="utf-8",
        )
