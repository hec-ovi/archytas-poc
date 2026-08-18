"""What every repository shares.

Each table has an `extra` JSON column so the client can add properties without a migration.
Rows come out with `extra` already decoded, and go in with it encoded, so nobody downstream
deals with JSON strings.
"""

from __future__ import annotations

from typing import Any, Iterable

from .database import Database, dumps, loads

JSON_COLUMNS = ("extra", "payload", "parsed", "raw", "candidates", "resolution", "summary", "value")


class Repository:
    """Small helpers over one table. Subclasses add the queries that mean something."""

    table: str = ""

    def __init__(self, db: Database):
        self.db = db

    # ------------------------------------------------------------------ reading

    def get(self, row_id: int) -> dict[str, Any] | None:
        return decode(self.db.one(f"SELECT * FROM {self.table} WHERE id = ?", (row_id,)))

    def get_by(self, column: str, value: Any) -> dict[str, Any] | None:
        return decode(self.db.one(f"SELECT * FROM {self.table} WHERE {column} = ?", (value,)))

    def all(self, order_by: str = "id") -> list[dict[str, Any]]:
        return decode_all(self.db.query(f"SELECT * FROM {self.table} ORDER BY {order_by}"))

    def count(self, where: str = "1=1", params: tuple = ()) -> int:
        return self.db.scalar(f"SELECT COUNT(*) FROM {self.table} WHERE {where}", params) or 0

    # ------------------------------------------------------------------ writing

    def insert(self, values: dict[str, Any]) -> int:
        columns, params = _prepare(values)
        placeholders = ", ".join("?" for _ in columns)
        cursor = self.db.execute(
            f"INSERT INTO {self.table} ({', '.join(columns)}) VALUES ({placeholders})", params
        )
        return int(cursor.lastrowid)

    def update(self, row_id: int, values: dict[str, Any]) -> None:
        if not values:
            return
        columns, params = _prepare(values)
        assignments = ", ".join(f"{column} = ?" for column in columns)
        self.db.execute(f"UPDATE {self.table} SET {assignments} WHERE id = ?", (*params, row_id))

    def upsert(self, values: dict[str, Any], conflict: Iterable[str]) -> int:
        """Insert, or update the row that already holds those key columns, and return its id."""
        conflict = tuple(conflict)
        columns, params = _prepare(values)
        placeholders = ", ".join("?" for _ in columns)
        updates = ", ".join(f"{c} = excluded.{c}" for c in columns if c not in conflict)
        sql = (
            f"INSERT INTO {self.table} ({', '.join(columns)}) VALUES ({placeholders}) "
            f"ON CONFLICT ({', '.join(conflict)}) DO UPDATE SET {updates or columns[0] + ' = ' + columns[0]} "
            f"RETURNING id"
        )
        row = self.db.execute(sql, params).fetchone()
        return int(row[0])

    def delete(self, row_id: int) -> None:
        self.db.execute(f"DELETE FROM {self.table} WHERE id = ?", (row_id,))


def decode(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {k: (loads(v) if k in JSON_COLUMNS else v) for k, v in row.items()}


def decode_all(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [decode(row) for row in rows]


def _prepare(values: dict[str, Any]) -> tuple[list[str], tuple]:
    columns = list(values)
    params = tuple(
        dumps(values[c]) if c in JSON_COLUMNS and not isinstance(values[c], str) else values[c]
        for c in columns
    )
    return columns, params
