"""The calendar of due dates.

Every invoice with a due date shows up here, plus anything a person adds by hand. Moving a
date keeps where it came from, because "this was rescheduled" is information the client
loses today.
"""

from __future__ import annotations

from typing import Any

from .base import Repository, decode_all


class CalendarRepository(Repository):
    table = "calendar_event"

    def save(self, values: dict[str, Any]) -> int:
        return self.insert(values)

    def between(self, start: str, end: str) -> list[dict[str, Any]]:
        """Everything due in a window, with enough context to draw a day cell."""
        return decode_all(
            self.db.query(
                """
                SELECT e.*, s.name AS supplier_name,
                       i.number AS invoice_number,
                       b.balance_cents, b.payment_state, b.has_receipt,
                       CAST(julianday(e.on_date) - julianday('now') AS INTEGER) AS days_ahead
                FROM calendar_event e
                LEFT JOIN supplier s        ON s.id = e.supplier_id
                LEFT JOIN invoice i         ON i.id = e.invoice_id
                LEFT JOIN invoice_balance b ON b.id = e.invoice_id
                WHERE e.on_date BETWEEN ? AND ?
                ORDER BY e.on_date, e.id
                """,
                (start, end),
            )
        )

    def for_invoice(self, invoice_id: int) -> dict[str, Any] | None:
        return self.get_by("invoice_id", invoice_id)

    def move(self, event_id: int, new_date: str, user: str) -> dict[str, Any] | None:
        current = self.get(event_id)
        if current is None:
            return None
        self.update(
            event_id,
            {
                "on_date": new_date,
                "moved_from": current.get("moved_from") or current["on_date"],
                "created_by": user,
                "updated_at": _now(),
            },
        )
        return self.get(event_id)

    def sync_from_invoice(self, invoice: dict[str, Any], supplier_id: int | None) -> int | None:
        """Keep one due-date entry per invoice, following the invoice's own date."""
        if not invoice.get("due_on"):
            return None
        existing = self.for_invoice(invoice["id"])
        values = {
            "title": f"Vence {invoice['number']}",
            "on_date": invoice["due_on"],
            "kind": "vencimiento",
            "invoice_id": invoice["id"],
            "supplier_id": supplier_id,
            "amount_cents": invoice.get("amount_cents"),
            "updated_at": _now(),
        }
        if existing is None:
            return self.insert(values)
        # a date a person moved by hand is not overwritten by the next sync
        if existing.get("moved_from"):
            values.pop("on_date")
        self.update(existing["id"], values)
        return existing["id"]


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
