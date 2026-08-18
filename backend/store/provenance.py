"""Where every number came from.

Each row the portal served is kept exactly as it arrived. Two reasons: normalization rules
change, and rerunning them on stored payloads is cheaper and safer than re-scraping; and
when the client asks "where does this figure come from", there is an answer.
"""

from __future__ import annotations

import hashlib
from typing import Any

from .base import Repository, decode_all
from .database import dumps


class RawRecordRepository(Repository):
    table = "raw_record"

    def record(self, dataset: str, external_id: str, payload: dict[str, Any]) -> int:
        encoded = dumps(payload)
        return self.upsert(
            {
                "dataset": dataset,
                "external_id": external_id,
                "payload": encoded,
                "content_hash": hashlib.sha256(encoded.encode("utf-8")).hexdigest(),
            },
            ["dataset", "external_id", "content_hash"],
        )

    def history(self, dataset: str, external_id: str) -> list[dict[str, Any]]:
        return decode_all(
            self.db.query(
                "SELECT * FROM raw_record WHERE dataset = ? AND external_id = ? ORDER BY fetched_at DESC",
                (dataset, external_id),
            )
        )


class SyncRunRepository(Repository):
    table = "sync_run"

    def start(self, trigger: str) -> int:
        return self.insert({"trigger": trigger, "status": "corriendo"})

    def finish(self, run_id: int, status: str, summary: dict[str, Any]) -> None:
        self.update(run_id, {"status": status, "summary": summary, "finished_at": _now()})

    def latest(self, limit: int = 10) -> list[dict[str, Any]]:
        return decode_all(self.db.query("SELECT * FROM sync_run ORDER BY id DESC LIMIT ?", (limit,)))

    def last_successful(self) -> dict[str, Any] | None:
        rows = decode_all(self.db.query("SELECT * FROM sync_run WHERE status = 'ok' ORDER BY id DESC LIMIT 1"))
        return rows[0] if rows else None


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
