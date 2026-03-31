from __future__ import annotations

from kms_bot.repositories.base import BaseRepository
from kms_bot.schemas.registry import DocumentRegistryRecord


class DocumentRegistryRepository(BaseRepository):

    _SELECT_COLUMNS = (
        "page_id, title, source_version, last_updated, raw_hash, chunk_count, "
        "pipeline_version, index_status, last_sync_time, last_index_time, error_message"
    )

    def count_all(self) -> int:
        row = self.fetch_one("SELECT COUNT(*) AS document_count FROM document_registry")
        if row is None:
            return 0
        return int(row["document_count"])

    def get_by_page_id(self, page_id: str) -> DocumentRegistryRecord | None:
        row = self.fetch_one(
            f"SELECT {self._SELECT_COLUMNS} FROM document_registry WHERE page_id = ?",
            (page_id,),
        )
        if row is None:
            return None
        return DocumentRegistryRecord.model_validate(row)

    def list_all(self) -> list[DocumentRegistryRecord]:
        rows = self.fetch_all(
            f"SELECT {self._SELECT_COLUMNS} FROM document_registry ORDER BY last_sync_time DESC"
        )
        return [DocumentRegistryRecord.model_validate(row) for row in rows]

    def get_latest_sync_time(self) -> str | None:
        row = self.fetch_one("SELECT MAX(last_sync_time) AS latest FROM document_registry")
        if row is None:
            return None
        return row.get("latest")

    def upsert(
        self,
        *,
        page_id: str,
        title: str,
        source_version: int,
        last_updated: str,
        raw_hash: str,
        pipeline_version: int,
        last_sync_time: str,
        error_message: str | None,
    ) -> None:
        self.execute(
            """
            INSERT INTO document_registry (
                page_id, title, source_version, last_updated, raw_hash,
                chunk_count, pipeline_version, index_status,
                last_sync_time, last_index_time, error_message
            ) VALUES (?, ?, ?, ?, ?, 0, ?, 'not_indexed', ?, NULL, ?)
            ON CONFLICT(page_id) DO UPDATE SET
                title            = excluded.title,
                source_version   = excluded.source_version,
                last_updated     = excluded.last_updated,
                raw_hash         = excluded.raw_hash,
                pipeline_version = excluded.pipeline_version,
                index_status     = CASE
                                     WHEN excluded.error_message IS NOT NULL THEN 'error'
                                     ELSE 'stale'
                                   END,
                last_sync_time   = excluded.last_sync_time,
                error_message    = excluded.error_message
            """,
            (
                page_id, title, source_version, last_updated, raw_hash,
                pipeline_version, last_sync_time, error_message,
            ),
        )