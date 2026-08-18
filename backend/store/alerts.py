"""Events worth telling someone about, and whether the telling worked.

An event is raised once and only once: `dedupe_key` is what stops the same due date from
being announced every hour. Delivery is kept apart from the event, so a message that failed
to send can be retried without the event firing again.
"""

from __future__ import annotations

from typing import Any

from .base import Repository, decode_all


class AlertRepository(Repository):
    table = "alert_event"

    def raise_event(self, values: dict[str, Any]) -> tuple[int, bool]:
        """Returns the event id and whether it is new. Only new events get sent."""
        existing = self.get_by("dedupe_key", values["dedupe_key"])
        if existing:
            return existing["id"], False
        return self.insert(values), True

    def recent(self, limit: int = 50) -> list[dict[str, Any]]:
        return decode_all(
            self.db.query("SELECT * FROM alert_event ORDER BY created_at DESC, id DESC LIMIT ?", (limit,))
        )

    def unacknowledged(self) -> list[dict[str, Any]]:
        return decode_all(
            self.db.query("SELECT * FROM alert_event WHERE acknowledged = 0 ORDER BY created_at DESC")
        )

    def acknowledge(self, event_id: int) -> None:
        self.update(event_id, {"acknowledged": 1})


class DeliveryRepository(Repository):
    table = "alert_delivery"

    def record(self, event_id: int, channel: str, recipient: str, status: str, detail: str = "") -> int:
        return self.upsert(
            {
                "event_id": event_id,
                "channel": channel,
                "recipient": recipient,
                "status": status,
                "detail": detail,
                "sent_at": _now() if status == "entregado" else None,
            },
            ["event_id", "channel", "recipient"],
        )

    def failed(self) -> list[dict[str, Any]]:
        return self.db.query(
            """
            SELECT d.*, e.title, e.severity
            FROM alert_delivery d JOIN alert_event e ON e.id = d.event_id
            WHERE d.status = 'fallido' ORDER BY d.id DESC
            """
        )

    def for_event(self, event_id: int) -> list[dict[str, Any]]:
        return self.db.query("SELECT * FROM alert_delivery WHERE event_id = ?", (event_id,))


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
