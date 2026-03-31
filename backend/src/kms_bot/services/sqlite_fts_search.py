"""SQLite FTS5 搜索服务 —— Azure AI Search 的本地替代实现。

使用 SQLite 内置的 FTS5 全文搜索引擎，支持 BM25 排序，零额外依赖。
当 Azure AI Search 不可用时，将此服务注入 SearchService 接口即可无缝切换。
"""

from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path

from kms_bot.core.settings import ApplicationSettings
from kms_bot.core.utils import make_job_id, utcnow
from kms_bot.db.sqlite import SQLiteDatabase
from kms_bot.repositories.document_registry import DocumentRegistryRepository
from kms_bot.schemas.common import OperationAcceptedResponse
from kms_bot.schemas.documents import ChunkRecord
from kms_bot.schemas.index import IndexStatusResponse
from kms_bot.schemas.query import SearchResultHit
from kms_bot.services.interfaces import SearchService

logger = logging.getLogger(__name__)

_CREATE_FTS_TABLE = """
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    chunk_id UNINDEXED,
    doc_id UNINDEXED,
    title,
    section,
    content,
    url UNINDEXED,
    tags_json UNINDEXED,
    pipeline_version UNINDEXED,
    tokenize='unicode61 remove_diacritics 2'
);
"""

_DROP_FTS_TABLE = "DROP TABLE IF EXISTS chunks_fts;"

_INSERT_CHUNK = """
INSERT INTO chunks_fts
    (chunk_id, doc_id, title, section, content, url, tags_json, pipeline_version)
VALUES (?, ?, ?, ?, ?, ?, ?, ?);
"""

_SEARCH_QUERY = """
SELECT chunk_id, doc_id, title, section, content, url, tags_json, pipeline_version,
       (-rank) AS score
FROM chunks_fts
WHERE chunks_fts MATCH ?
ORDER BY rank
LIMIT ?;
"""


class _IndexState:
    def __init__(self, pipeline_version: int) -> None:
        self.status: str = "idle"
        self.current_job_id: str | None = None
        self.pipeline_version: int = pipeline_version
        self.last_started_at: datetime | None = None
        self.last_finished_at: datetime | None = None
        self.last_success_at: datetime | None = None
        self.indexed_documents: int = 0
        self.indexed_chunks: int = 0
        self.error_message: str | None = None

    def to_response(self) -> IndexStatusResponse:
        return IndexStatusResponse(
            status=self.status,
            current_job_id=self.current_job_id,
            pipeline_version=self.pipeline_version,
            last_started_at=self.last_started_at,
            last_finished_at=self.last_finished_at,
            last_success_at=self.last_success_at,
            indexed_documents=self.indexed_documents,
            indexed_chunks=self.indexed_chunks,
            error_message=self.error_message,
        )


def _sanitize_fts_query(raw: str) -> str:
    """将用户输入安全地转换为 FTS5 MATCH 表达式。

    FTS5 特殊字符（" * ^ ( ) - + :）会被去除，每个词项用双引号包裹。
    """
    special = set('"*^()-+:')
    cleaned = "".join(c if c not in special else " " for c in raw)
    terms = [t.strip() for t in cleaned.split() if t.strip()]
    if not terms:
        return '""'
    return " ".join(f'"{t}"' for t in terms)


class SQLiteFTSSearchService(SearchService):
    """基于 SQLite FTS5 的全文搜索实现，替代 Azure AI Search。

    - Rebuild Index：删除并重建 chunks_fts 虚拟表，从 data/chunks/*.chunks.json 批量导入。
    - Search：通过 FTS5 MATCH 执行 BM25 关键词检索，返回 SearchResultHit 列表。
    """

    def __init__(
        self,
        *,
        settings: ApplicationSettings,
        database: SQLiteDatabase,
        registry_repository: DocumentRegistryRepository,
    ) -> None:
        self._settings = settings
        self._database = database
        self._registry = registry_repository
        self._chunks_dir: Path = settings.resolve_path(settings.storage.chunks_dir)
        self._state = _IndexState(settings.app.pipeline_version)
        self._lock = asyncio.Lock()

    def initialize_table(self) -> None:
        """在数据库初始化之后调用，确保 FTS5 虚拟表存在。"""
        with self._database.connection() as conn:
            conn.executescript(_CREATE_FTS_TABLE)
            conn.commit()
        logger.info("fts_table_initialized")

    # ── SearchService.search ──────────────────────────────────

    async def search(self, *, query: str, top_k: int) -> list[SearchResultHit]:
        fts_query = _sanitize_fts_query(query)
        try:
            rows = await asyncio.to_thread(
                self._database.fetch_all, _SEARCH_QUERY, (fts_query, top_k)
            )
        except sqlite3.OperationalError as exc:
            logger.warning("fts_search_error", extra={"query": query, "error": str(exc)})
            return []

        hits: list[SearchResultHit] = []
        for row in rows:
            tags = json.loads(row["tags_json"]) if row["tags_json"] else []
            hits.append(
                SearchResultHit(
                    chunk_id=row["chunk_id"],
                    doc_id=row["doc_id"],
                    title=row["title"],
                    section=row["section"],
                    content=row["content"],
                    url=row["url"],
                    tags=tags,
                    pipeline_version=int(row["pipeline_version"]),
                    score=float(row["score"]),
                )
            )
        logger.info(
            "fts_search_completed",
            extra={"query": query, "top_k": top_k, "hits": len(hits)},
        )
        return hits

    # ── SearchService.rebuild_index ───────────────────────────

    async def rebuild_index(self) -> OperationAcceptedResponse:
        if self._state.status == "running":
            return OperationAcceptedResponse(
                job_id=self._state.current_job_id or "unknown",
                job_type="index_rebuild",
                status="accepted",
                requested_at=utcnow(),
                pipeline_version=self._settings.app.pipeline_version,
                message="Index rebuild is already running.",
            )
        job_id = make_job_id("fts-rebuild")
        asyncio.create_task(self._run_rebuild(job_id))
        return OperationAcceptedResponse(
            job_id=job_id,
            job_type="index_rebuild",
            status="accepted",
            requested_at=utcnow(),
            pipeline_version=self._settings.app.pipeline_version,
            message="SQLite FTS5 index rebuild accepted.",
        )

    # ── SearchService.get_index_status ────────────────────────

    async def get_index_status(self) -> IndexStatusResponse:
        return self._state.to_response()

    # ── background rebuild ────────────────────────────────────

    async def _run_rebuild(self, job_id: str) -> None:
        async with self._lock:
            self._state.status = "running"
            self._state.current_job_id = job_id
            self._state.last_started_at = utcnow()
            self._state.error_message = None

            try:
                # 1. 删除并重建 FTS5 表
                await asyncio.to_thread(self._reset_fts_table)

                # 2. 从磁盘加载所有 chunk 文件
                all_chunks = self._load_all_chunks()

                # 3. 批量写入
                await asyncio.to_thread(self._insert_chunks, all_chunks)

                # 4. 更新注册表状态
                now = utcnow().isoformat()
                doc_ids = {c.doc_id for c in all_chunks}
                for doc_id in doc_ids:
                    self._registry.update_index_status(
                        page_id=doc_id,
                        index_status="indexed",
                        last_index_time=now,
                    )

                self._state.indexed_documents = len(doc_ids)
                self._state.indexed_chunks = len(all_chunks)
                self._state.status = "success"
                self._state.last_success_at = utcnow()
                logger.info(
                    "fts_rebuild_completed",
                    extra={
                        "job_id": job_id,
                        "documents": len(doc_ids),
                        "chunks": len(all_chunks),
                    },
                )
            except Exception as exc:
                self._state.status = "error"
                self._state.error_message = str(exc)
                logger.error(
                    "fts_rebuild_failed",
                    extra={"job_id": job_id, "error": str(exc)},
                    exc_info=True,
                )
            finally:
                self._state.last_finished_at = utcnow()

    # ── helpers ───────────────────────────────────────────────

    def _reset_fts_table(self) -> None:
        with self._database.connection() as conn:
            conn.executescript(f"{_DROP_FTS_TABLE}\n{_CREATE_FTS_TABLE}")
            conn.commit()

    def _insert_chunks(self, chunks: list[ChunkRecord]) -> None:
        rows = [
            (
                c.chunk_id,
                c.doc_id,
                c.title,
                c.section,
                c.content,
                str(c.url),
                json.dumps(c.tags, ensure_ascii=False),
                c.pipeline_version,
            )
            for c in chunks
        ]
        with self._database.connection() as conn:
            conn.executemany(_INSERT_CHUNK, rows)
            conn.commit()

    def _load_all_chunks(self) -> list[ChunkRecord]:
        chunks: list[ChunkRecord] = []
        if not self._chunks_dir.exists():
            logger.info("chunks_dir_missing", extra={"path": str(self._chunks_dir)})
            return chunks

        for chunk_file in sorted(self._chunks_dir.glob("*.chunks.json")):
            try:
                raw = json.loads(chunk_file.read_text(encoding="utf-8"))
                for item in raw:
                    chunks.append(ChunkRecord.model_validate(item))
            except Exception as exc:
                logger.warning(
                    "chunk_file_load_error",
                    extra={"file": str(chunk_file), "error": str(exc)},
                )
        logger.info("chunks_loaded", extra={"total": len(chunks)})
        return chunks
