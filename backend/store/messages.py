"""The inbox nobody opens.

Two things land here: the portal's own warnings, and suppliers writing to say we owe them.
The client's problem is not that the messages are missing, it is that they are only in a
place nobody visits. So the useful query is not "list messages", it is "what is still
unresolved".
"""

from __future__ import annotations

from typing import Any

from .base import Repository, decode_all


class MessageRepository(Repository):
    table = "message"

    def save(self, values: dict[str, Any]) -> int:
        return self.upsert(values, ["external_id"])

    def listing(self, only_open: bool = False) -> list[dict[str, Any]]:
        where = "WHERE m.resolved = 0" if only_open else ""
        return decode_all(
            self.db.query(
                f"""
                SELECT m.*, s.name AS supplier_name, i.number AS invoice_number,
                       p.code AS product_code
                FROM message m
                LEFT JOIN supplier s ON s.id = m.supplier_id
                LEFT JOIN invoice i  ON i.id = m.invoice_id
                LEFT JOIN product p  ON p.id = m.product_id
                {where}
                ORDER BY m.received_on DESC, m.id DESC
                """
            )
        )

    def resolve(self, message_id: int, user: str) -> None:
        self.update(message_id, {"resolved": 1, "resolved_by": user, "resolved_at": _now()})

    def open_count(self) -> int:
        return self.count("resolved = 0")

    def by_kind(self) -> list[dict[str, Any]]:
        return self.db.query(
            "SELECT kind, COUNT(*) AS n, SUM(CASE WHEN resolved = 0 THEN 1 ELSE 0 END) AS open "
            "FROM message GROUP BY kind ORDER BY n DESC"
        )


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
