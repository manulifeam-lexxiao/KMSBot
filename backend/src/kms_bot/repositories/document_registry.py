from __future__ import annotations

from kms_bot.repositories.base import BaseRepository
from kms_bot.schemas.registry import DocumentRegistryRecord


class DocumentRegistryRepository(BaseRepository):
    def count_all(self) -> int:
        row = self.fetch_one("SELECT COUNT(*) AS document_count FROM document_registry")
        if row is None:
            return 0
        return int(row["document_count"])

    def get_by_page_id(self, page_id: str) -> DocumentRegistryRecord | None:
        row = self.fetch_one(
            "SELECT page_id, title, source_version, last_updated, raw_hash, chunk_count, pipeline_version, "
            "index_status, last_sync_time, last_index_time, error_message "
            "FROM document_registry WHERE page_id = ?",
            (page_id,),
        )
        if row is None:
            return None
        return DocumentRegistryRecord.model_validate(row)