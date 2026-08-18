"""The SQLite connection and how the schema gets there.

One file on disk, WAL journal so a read never blocks the sync writing behind it. The schema
is plain SQL applied with `CREATE TABLE IF NOT EXISTS`, so opening an existing database is
the same operation as creating a new one.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

SCHEMA_FILE = Path(__file__).with_name("schema.sql")


class Database:
    """Owns the connection and hands out cursors. Repositories borrow it, never open one."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.path, check_same_thread=False, isolation_level=None)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute("PRAGMA journal_mode = WAL")
        self._connection.execute("PRAGMA busy_timeout = 5000")

    def create_schema(self) -> None:
        self._connection.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Everything inside lands together or not at all."""
        self._connection.execute("BEGIN")
        try:
            yield self._connection
        except Exception:
            self._connection.execute("ROLLBACK")
            raise
        else:
            self._connection.execute("COMMIT")

    def query(self, sql: str, params: tuple | dict = ()) -> list[dict[str, Any]]:
        return [dict(row) for row in self._connection.execute(sql, params)]

    def one(self, sql: str, params: tuple | dict = ()) -> dict[str, Any] | None:
        row = self._connection.execute(sql, params).fetchone()
        return dict(row) if row else None

    def scalar(self, sql: str, params: tuple | dict = ()) -> Any:
        row = self._connection.execute(sql, params).fetchone()
        return row[0] if row else None

    def execute(self, sql: str, params: tuple | dict = ()) -> sqlite3.Cursor:
        return self._connection.execute(sql, params)

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, *_) -> None:
        self.close()


def loads(value: Any) -> Any:
    """Read a JSON column. A broken one reads as empty rather than taking down a page."""
    if not value:
        return {}
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return {}


def dumps(value: Any) -> str:
    return json.dumps(value or {}, ensure_ascii=False, sort_keys=True)
