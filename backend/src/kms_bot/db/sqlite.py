from __future__ import annotations

import sqlite3
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from kms_bot.core.settings import ApplicationSettings


class SQLiteDatabase:
    def __init__(self, settings: ApplicationSettings) -> None:
        self._settings = settings
        self._bootstrap_sql_path = settings.resolve_path("config/contracts/sqlite/001_registry.sql")
        self._migration_paths = [
            settings.resolve_path("config/contracts/sqlite/002_add_labels_and_tokens.sql"),
        ]

    @property
    def database_url(self) -> str:
        return self._settings.database.url

    @property
    def database_path(self) -> Path:
        url = self.database_url
        prefix = "sqlite:///"
        if not url.startswith(prefix):
            raise ValueError("Only sqlite:/// URLs are supported by the baseline runtime.")

        raw_path = url[len(prefix) :]
        if raw_path == ":memory:":
            return Path(raw_path)

        path = Path(raw_path)
        if path.is_absolute():
            return path
        return (self._settings.repo_root / path).resolve()

    def initialize(self) -> None:
        for directory in self._settings.data_directories:
            directory.mkdir(parents=True, exist_ok=True)

        if self.database_path != Path(":memory:"):
            self.database_path.parent.mkdir(parents=True, exist_ok=True)

        schema_sql = self._bootstrap_sql_path.read_text(encoding="utf-8")
        with self.connection() as connection:
            connection.executescript(schema_sql)
            connection.commit()

        # 运行增量迁移（幂等：ALTER 失败时跳过已存在的列）
        for migration_path in self._migration_paths:
            if migration_path.exists():
                self._apply_migration(migration_path)

    def _apply_migration(self, migration_path: Path) -> None:
        """逐条执行迁移SQL，跳过已完成的DDL语句（如重复的ALTER TABLE）。"""
        sql = migration_path.read_text(encoding="utf-8")
        with self.connection() as connection:
            for statement in sql.split(";"):
                # 去除注释行后判断是否有实际 SQL
                lines = [
                    line
                    for line in statement.splitlines()
                    if line.strip() and not line.strip().startswith("--")
                ]
                actual_sql = "\n".join(lines).strip()
                if not actual_sql:
                    continue
                try:
                    connection.execute(statement)
                except sqlite3.OperationalError as exc:
                    # 跳过 "duplicate column" 等幂等错误
                    if "duplicate column" in str(exc).lower():
                        continue
                    if "already exists" in str(exc).lower():
                        continue
                    raise
            connection.commit()

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        database_name = (
            ":memory:" if self.database_path == Path(":memory:") else str(self.database_path)
        )
        connection = sqlite3.connect(database_name, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON;")
        try:
            yield connection
        finally:
            connection.close()

    def execute(self, query: str, parameters: Sequence[Any] | None = None) -> None:
        with self.connection() as connection:
            connection.execute(query, tuple(parameters or ()))
            connection.commit()

    def fetch_one(self, query: str, parameters: Sequence[Any] | None = None) -> sqlite3.Row | None:
        with self.connection() as connection:
            cursor = connection.execute(query, tuple(parameters or ()))
            return cursor.fetchone()

    def fetch_all(self, query: str, parameters: Sequence[Any] | None = None) -> list[sqlite3.Row]:
        with self.connection() as connection:
            cursor = connection.execute(query, tuple(parameters or ()))
            return cursor.fetchall()

    def ping(self) -> bool:
        try:
            row = self.fetch_one("SELECT 1 AS ok")
        except sqlite3.Error:
            return False
        return row is not None and int(row["ok"]) == 1
