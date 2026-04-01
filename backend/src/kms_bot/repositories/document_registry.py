from __future__ import annotations

import json

from kms_bot.repositories.base import BaseRepository
from kms_bot.schemas.registry import DocumentRegistryRecord


class DocumentRegistryRepository(BaseRepository):
    _SELECT_COLUMNS = (
        "page_id, title, source_version, last_updated, raw_hash, chunk_count, "
        "pipeline_version, index_status, last_sync_time, last_index_time, error_message, labels"
    )

    def count_all(self) -> int:
        row = self.fetch_one("SELECT COUNT(*) AS document_count FROM document_registry")
        if row is None:
            return 0
        return int(row["document_count"])

    def delete_all(self) -> None:
        """删除 document_registry 中所有记录（用于 Full Sync 清空）。"""
        self.execute("DELETE FROM document_registry")

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

    def update_chunk_count(self, *, page_id: str, chunk_count: int) -> None:
        """Set chunk_count and mark the document as stale for re-indexing."""
        self.execute(
            """
            UPDATE document_registry
               SET chunk_count   = ?,
                   index_status  = 'stale'
             WHERE page_id = ?
            """,
            (chunk_count, page_id),
        )

    def update_index_status(
        self, *, page_id: str, index_status: str, last_index_time: str | None = None
    ) -> None:
        """Update the index_status (and optionally last_index_time) for a document."""
        self.execute(
            """
            UPDATE document_registry
               SET index_status   = ?,
                   last_index_time = COALESCE(?, last_index_time)
             WHERE page_id = ?
            """,
            (index_status, last_index_time, page_id),
        )

    def count_by_index_status(self, index_status: str) -> int:
        row = self.fetch_one(
            "SELECT COUNT(*) AS cnt FROM document_registry WHERE index_status = ?",
            (index_status,),
        )
        if row is None:
            return 0
        return int(row["cnt"])

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
        labels: str = "[]",
    ) -> None:
        self.execute(
            """
            INSERT INTO document_registry (
                page_id, title, source_version, last_updated, raw_hash,
                chunk_count, pipeline_version, index_status,
                last_sync_time, last_index_time, error_message, labels
            ) VALUES (?, ?, ?, ?, ?, 0, ?, 'not_indexed', ?, NULL, ?, ?)
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
                error_message    = excluded.error_message,
                labels           = excluded.labels
            """,
            (
                page_id,
                title,
                source_version,
                last_updated,
                raw_hash,
                pipeline_version,
                last_sync_time,
                error_message,
                labels,
            ),
        )

    def get_summary_stats(self) -> dict:
        """获取知识库元数据摘要：文档数量、标题列表、标签分布等。"""
        total = self.count_all()

        rows = self.fetch_all(
            "SELECT page_id, title, labels, chunk_count FROM document_registry ORDER BY title"
        )

        titles: list[str] = []
        label_counts: dict[str, int] = {}
        total_chunks = 0
        for row in rows:
            titles.append(row["title"])
            total_chunks += row.get("chunk_count", 0) or 0
            try:
                labels = json.loads(row.get("labels", "[]"))
                for label in labels:
                    label_counts[label] = label_counts.get(label, 0) + 1
            except (json.JSONDecodeError, TypeError):
                continue

        return {
            "total_documents": total,
            "total_chunks": total_chunks,
            "titles": titles,
            "label_distribution": label_counts,
        }
