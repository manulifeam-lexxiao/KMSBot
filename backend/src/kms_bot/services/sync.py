from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from kms_bot.core.errors import AppError
from kms_bot.core.settings import ApplicationSettings
from kms_bot.repositories.document_registry import DocumentRegistryRepository
from kms_bot.schemas.common import OperationAcceptedResponse
from kms_bot.schemas.sync import SyncStatusResponse
from kms_bot.services.confluence_client import ConfluenceClient, ConfluencePage
from kms_bot.services.interfaces import SyncService

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _job_id(prefix: str) -> str:
    return f"{prefix}-{_utcnow().strftime('%Y%m%d%H%M%S')}"


def _compute_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


class _SyncState:
    """In-memory tracker for the latest sync run status."""

    def __init__(self, pipeline_version: int) -> None:
        self.status: str = "idle"
        self.mode: str = "none"
        self.current_job_id: str | None = None
        self.pipeline_version: int = pipeline_version
        self.last_started_at: datetime | None = None
        self.last_finished_at: datetime | None = None
        self.last_success_at: datetime | None = None
        self.processed_pages: int = 0
        self.changed_pages: int = 0
        self.error_message: str | None = None

    def to_response(self) -> SyncStatusResponse:
        return SyncStatusResponse(
            status=self.status,
            mode=self.mode,
            current_job_id=self.current_job_id,
            pipeline_version=self.pipeline_version,
            last_started_at=self.last_started_at,
            last_finished_at=self.last_finished_at,
            last_success_at=self.last_success_at,
            processed_pages=self.processed_pages,
            changed_pages=self.changed_pages,
            error_message=self.error_message,
        )


class ConfluenceSyncService(SyncService):
    """Real Confluence sync service that fetches pages and stores raw content."""

    def __init__(
        self,
        *,
        settings: ApplicationSettings,
        confluence_client: ConfluenceClient,
        registry_repository: DocumentRegistryRepository,
    ) -> None:
        self._settings = settings
        self._client = confluence_client
        self._registry = registry_repository
        self._raw_dir: Path = settings.resolve_path(settings.storage.raw_dir)
        self._state = _SyncState(settings.app.pipeline_version)
        self._lock = asyncio.Lock()

    # ── public interface ──────────────────────────────────────

    async def trigger_full_sync(self) -> OperationAcceptedResponse:
        self._assert_configured()
        self._assert_not_running()
        job_id = _job_id("sync-full")
        asyncio.create_task(self._run_sync(mode="full", job_id=job_id))
        return self._accepted("full_sync", job_id, "Full sync request accepted.")

    async def trigger_incremental_sync(self) -> OperationAcceptedResponse:
        self._assert_configured()
        self._assert_not_running()
        job_id = _job_id("sync-incremental")
        asyncio.create_task(self._run_sync(mode="incremental", job_id=job_id))
        return self._accepted("incremental_sync", job_id, "Incremental sync request accepted.")

    async def get_status(self) -> SyncStatusResponse:
        return self._state.to_response()

    # ── guards ────────────────────────────────────────────────

    def _assert_configured(self) -> None:
        if not self._client.is_configured:
            raise AppError(
                error_code="confluence_not_configured",
                message="Confluence connection settings are incomplete. "
                        "Set base_url, space_key, username, and api_token.",
                status_code=400,
            )

    def _assert_not_running(self) -> None:
        if self._state.status == "running":
            raise AppError(
                error_code="sync_already_running",
                message="A sync operation is already in progress.",
                status_code=409,
            )

    # ── background sync runner ────────────────────────────────

    async def _run_sync(self, *, mode: str, job_id: str) -> None:
        async with self._lock:
            self._state.status = "running"
            self._state.mode = mode
            self._state.current_job_id = job_id
            self._state.last_started_at = _utcnow()
            self._state.processed_pages = 0
            self._state.changed_pages = 0
            self._state.error_message = None

            try:
                pages = await self._fetch_pages(mode)

                for page in pages:
                    self._process_page(page)
                    self._state.processed_pages += 1

                self._state.status = "success"
                self._state.last_success_at = _utcnow()
                logger.info(
                    "sync_completed",
                    extra={
                        "mode": mode,
                        "job_id": job_id,
                        "processed": self._state.processed_pages,
                        "changed": self._state.changed_pages,
                    },
                )
            except Exception as exc:
                self._state.status = "error"
                self._state.error_message = str(exc)
                logger.exception("sync_failed", extra={"mode": mode, "job_id": job_id})
            finally:
                self._state.last_finished_at = _utcnow()
                self._state.current_job_id = None

    async def _fetch_pages(self, mode: str) -> list[ConfluencePage]:
        if mode == "full":
            return await self._client.fetch_all_pages()

        since = self._registry.get_latest_sync_time()
        if since:
            return await self._client.fetch_pages_updated_since(since)

        logger.info("no_previous_sync_falling_back_to_full")
        return await self._client.fetch_all_pages()

    # ── per-page processing ───────────────────────────────────

    def _process_page(self, page: ConfluencePage) -> None:
        try:
            raw_hash = _compute_hash(page.body_html)
            now_iso = _utcnow().isoformat()

            existing = self._registry.get_by_page_id(page.page_id)
            if (
                existing
                and existing.raw_hash == raw_hash
                and existing.source_version == page.source_version
            ):
                logger.debug("page_unchanged", extra={"page_id": page.page_id})
                return

            self._store_raw(page, raw_hash, now_iso)

            self._registry.upsert(
                page_id=page.page_id,
                title=page.title,
                source_version=page.source_version,
                last_updated=page.last_updated or now_iso,
                raw_hash=raw_hash,
                pipeline_version=self._settings.app.pipeline_version,
                last_sync_time=now_iso,
                error_message=None,
            )
            self._state.changed_pages += 1
            logger.info("page_synced", extra={"page_id": page.page_id, "title": page.title})

        except Exception as exc:
            logger.warning("page_sync_error", extra={"page_id": page.page_id, "error": str(exc)})
            self._registry.upsert(
                page_id=page.page_id,
                title=page.title or page.page_id,
                source_version=page.source_version,
                last_updated=page.last_updated or _utcnow().isoformat(),
                raw_hash="",
                pipeline_version=self._settings.app.pipeline_version,
                last_sync_time=_utcnow().isoformat(),
                error_message=str(exc),
            )

    def _store_raw(self, page: ConfluencePage, raw_hash: str, sync_time: str) -> None:
        self._raw_dir.mkdir(parents=True, exist_ok=True)

        # Raw HTML file
        html_path = self._raw_dir / f"{page.page_id}.html"
        html_path.write_text(page.body_html, encoding="utf-8")

        # Metadata sidecar JSON (enables parser to run independently)
        meta = {
            "page_id": page.page_id,
            "title": page.title,
            "source_version": page.source_version,
            "last_updated": page.last_updated,
            "url": page.url,
            "raw_hash": raw_hash,
            "sync_time": sync_time,
            "pipeline_version": self._settings.app.pipeline_version,
        }
        meta_path = self._raw_dir / f"{page.page_id}.meta.json"
        meta_path.write_text(
            json.dumps(meta, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    # ── helpers ────────────────────────────────────────────────

    def _accepted(self, job_type: str, job_id: str, message: str) -> OperationAcceptedResponse:
        return OperationAcceptedResponse(
            job_id=job_id,
            job_type=job_type,
            status="accepted",
            requested_at=_utcnow(),
            pipeline_version=self._settings.app.pipeline_version,
            message=message,
        )
