"""标题搜索服务 —— 基于 titles_fts 表进行 L0 快速搜索。"""

from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
from dataclasses import dataclass

from kms_bot.db.sqlite import SQLiteDatabase

logger = logging.getLogger(__name__)

_SEARCH_TITLES = """
SELECT page_id, title, labels,
       (-rank) AS score
FROM titles_fts
WHERE titles_fts MATCH ?
ORDER BY rank
LIMIT ?;
"""

_SEARCH_ALL_TITLES = """
SELECT page_id, title, labels FROM document_registry ORDER BY title;
"""


@dataclass(frozen=True, slots=True)
class TitleSearchHit:
    """标题搜索结果。"""

    page_id: str
    title: str
    labels: list[str]
    score: float


def _sanitize_fts_query(raw: str) -> str:
    """将搜索词转换为 FTS5 安全的 MATCH 表达式（OR + 前缀匹配）。

    使用前缀匹配（term*）可提高英文词形变化的标题搜索召回率。
    """
    special = set('"*^()-+:')
    cleaned = "".join(c if c not in special else " " for c in raw)
    terms = [t.strip() for t in cleaned.split() if len(t.strip()) >= 2]
    if not terms:
        fallback = cleaned.strip()
        return f"{fallback}*" if fallback else '""'
    return " OR ".join(f"{t}*" for t in terms)


class TitleSearchService:
    """基于 FTS5 titles_fts 表的标题搜索服务。"""

    def __init__(self, database: SQLiteDatabase) -> None:
        self._database = database

    async def search(self, *, query: str, top_k: int = 20) -> list[TitleSearchHit]:
        """在 titles_fts 中搜索，返回匹配的标题。"""
        fts_query = _sanitize_fts_query(query)
        logger.info("title_search", extra={"fts_query": fts_query, "top_k": top_k})

        try:
            rows = await asyncio.to_thread(
                self._database.fetch_all, _SEARCH_TITLES, (fts_query, top_k)
            )
        except sqlite3.OperationalError as exc:
            logger.warning("title_search_error", extra={"query": query, "error": str(exc)})
            return []

        hits: list[TitleSearchHit] = []
        for row in rows:
            labels = json.loads(row["labels"]) if row["labels"] else []
            hits.append(
                TitleSearchHit(
                    page_id=row["page_id"],
                    title=row["title"],
                    labels=labels,
                    score=float(row["score"]),
                )
            )
        logger.info("title_search_completed", extra={"hits": len(hits)})
        return hits

    async def search_by_terms(self, terms: list[str], *, top_k: int = 20) -> list[TitleSearchHit]:
        """用多个搜索词进行联合搜索。"""
        combined = " ".join(terms)
        return await self.search(query=combined, top_k=top_k)
