"""The queue of things the system refused to guess.

"If something cannot be resolved on its own, tell us instead of guessing wrong." That
sentence is this table. Anything the normalizer could not settle lands here with what it
saw and what it suspects, and a person closes it in one click. A resolution is applied and
also remembered, so the same spelling never has to be asked about twice.
"""

from __future__ import annotations

from typing import Any

from .base import Repository, decode_all


class ReviewRepository(Repository):
    table = "review_item"

    def raise_item(self, values: dict[str, Any]) -> int:
        """Open an item, or leave the existing one alone if it is already open."""
        return self.upsert({**values, "status": values.get("status", "pendiente")}, ["dedupe_key"])

    def pending(self, kind: str | None = None) -> list[dict[str, Any]]:
        clause = "AND kind = ?" if kind else ""
        params = (kind,) if kind else ()
        return decode_all(
            self.db.query(
                f"SELECT * FROM review_item WHERE status = 'pendiente' {clause} ORDER BY created_at DESC",
                params,
            )
        )

    def resolve(self, item_id: int, resolution: dict[str, Any], user: str) -> None:
        self.update(item_id, {"status": "resuelto", "resolution": resolution, "resolved_by": user, "resolved_at": _now()})

    def dismiss(self, item_id: int, user: str) -> None:
        self.update(item_id, {"status": "descartado", "resolved_by": user, "resolved_at": _now()})

    def summary(self) -> list[dict[str, Any]]:
        return self.db.query(
            "SELECT kind, COUNT(*) AS n FROM review_item WHERE status = 'pendiente' GROUP BY kind ORDER BY n DESC"
        )

    def pending_count(self) -> int:
        return self.count("status = 'pendiente'")


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
