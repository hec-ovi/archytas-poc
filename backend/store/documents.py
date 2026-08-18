"""Files that came in, and anything that does not have a table yet.

An uploaded invoice lands here first with its hash, so the same file arriving twice is
recognised instead of loaded twice. What was extracted from it lives in `parsed` as JSON
until a person or the agent applies it to a real invoice.

This is also where a document type nobody planned for goes: it gets a `kind` and its fields
in `parsed`, with no migration.
"""

from __future__ import annotations

import hashlib
from typing import Any

from .base import Repository, decode, decode_all


class DocumentRepository(Repository):
    table = "document"

    def save(self, values: dict[str, Any]) -> int:
        return self.upsert(values, ["content_hash"])

    def by_hash(self, content_hash: str) -> dict[str, Any] | None:
        return self.get_by("content_hash", content_hash)

    def listing(self, kind: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
        clauses, params = ["1=1"], []
        if kind:
            clauses.append("kind = ?")
            params.append(kind)
        if status:
            clauses.append("status = ?")
            params.append(status)
        return decode_all(
            self.db.query(
                f"SELECT * FROM document WHERE {' AND '.join(clauses)} ORDER BY created_at DESC",
                tuple(params),
            )
        )

    def mark(self, document_id: int, status: str, invoice_id: int | None = None) -> None:
        values: dict[str, Any] = {"status": status}
        if invoice_id is not None:
            values["invoice_id"] = invoice_id
        self.update(document_id, values)


def content_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()
