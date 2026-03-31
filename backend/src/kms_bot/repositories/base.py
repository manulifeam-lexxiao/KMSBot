from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from kms_bot.db.sqlite import SQLiteDatabase


class BaseRepository:
    def __init__(self, database: SQLiteDatabase) -> None:
        self._database = database

    def fetch_one(
        self, query: str, parameters: Sequence[Any] | None = None
    ) -> dict[str, Any] | None:
        row = self._database.fetch_one(query, parameters)
        if row is None:
            return None
        return dict(row)

    def fetch_all(
        self, query: str, parameters: Sequence[Any] | None = None
    ) -> list[dict[str, Any]]:
        rows = self._database.fetch_all(query, parameters)
        return [dict(row) for row in rows]

    def execute(self, query: str, parameters: Sequence[Any] | None = None) -> None:
        self._database.execute(query, parameters)
