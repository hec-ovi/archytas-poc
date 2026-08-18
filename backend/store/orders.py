"""Purchase orders, and the ones nobody followed up on.

"I end up ordering the same thing twice because nobody remembered the first order." So an
order is not just a record: it has an age, and an order sitting unconfirmed for weeks is the
thing worth showing.
"""

from __future__ import annotations

from typing import Any

from .base import Repository, decode_all

# what the portal writes, grouped into the three states that matter to the client
OPEN_STATES = ("pendiente", "confirmada")
CLOSED_STATES = ("recibida", "anulada")


class PurchaseOrderRepository(Repository):
    table = "purchase_order"

    def save(self, values: dict[str, Any]) -> int:
        return self.upsert(values, ["external_id"] if values.get("external_id") else ["number"])

    def listing(self) -> list[dict[str, Any]]:
        return decode_all(
            self.db.query(
                """
                SELECT o.*, s.name AS supplier_name, s.slug AS supplier_slug,
                       p.code AS product_code, p.description AS product_description,
                       CAST(julianday('now') - julianday(o.ordered_on) AS INTEGER) AS age_days
                FROM purchase_order o
                LEFT JOIN supplier s ON s.id = o.supplier_id
                LEFT JOIN product p  ON p.id = o.product_id
                ORDER BY o.ordered_on DESC
                """
            )
        )

    def stale(self, older_than_days: int = 30) -> list[dict[str, Any]]:
        """Open orders that have been waiting too long. These are the ones that get reordered."""
        return decode_all(
            self.db.query(
                """
                SELECT o.*, s.name AS supplier_name,
                       CAST(julianday('now') - julianday(o.ordered_on) AS INTEGER) AS age_days
                FROM purchase_order o
                LEFT JOIN supplier s ON s.id = o.supplier_id
                WHERE o.status NOT IN ('recibida', 'anulada')
                  AND julianday('now') - julianday(o.ordered_on) > ?
                ORDER BY o.ordered_on
                """,
                (older_than_days,),
            )
        )

    def by_state(self) -> list[dict[str, Any]]:
        return self.db.query(
            """
            SELECT status, COUNT(*) AS n, COALESCE(SUM(estimated_cents), 0) AS cents
            FROM purchase_order GROUP BY status ORDER BY n DESC
            """
        )
