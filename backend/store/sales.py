"""Sales, and the ones that must not be counted.

The client's complaint is precise: some sales were loaded twice, others arrived broken, and
today both get summed as if they were real. So every row carries a status, and every number
the dashboard shows comes from `sale_valid`, which only contains what can be trusted.
"""

from __future__ import annotations

from typing import Any

from .base import Repository, decode_all


class SaleRepository(Repository):
    table = "sale"

    def save(self, values: dict[str, Any]) -> int:
        return self.upsert(values, ["code", "row_hash"])

    def flag(self, sale_id: int, status: str, note: str) -> None:
        self.update(sale_id, {"status": status, "status_note": note})

    def by_code(self, code: str) -> list[dict[str, Any]]:
        return decode_all(self.db.query("SELECT * FROM sale WHERE code = ? ORDER BY id", (code,)))

    def excluded(self) -> list[dict[str, Any]]:
        """Everything left out of the totals, with the reason. Nothing disappears quietly."""
        return decode_all(
            self.db.query(
                """
                SELECT s.*, p.code AS product_code, p.description AS product_description
                FROM sale s LEFT JOIN product p ON p.id = s.product_id
                WHERE s.status <> 'valida'
                ORDER BY s.status, s.code
                """
            )
        )

    def revenue_by_month(self) -> list[dict[str, Any]]:
        return self.db.query(
            """
            SELECT substr(sold_on, 1, 7) AS month,
                   COUNT(*)              AS sale_count,
                   SUM(total_cents)      AS revenue_cents,
                   SUM(quantity)         AS units
            FROM sale_valid
            WHERE sold_on IS NOT NULL AND sold_on <> ''
            GROUP BY month
            ORDER BY month
            """
        )

    def revenue_by_category(self) -> list[dict[str, Any]]:
        return self.db.query(
            """
            SELECT COALESCE(c.name, 'Sin rubro') AS category,
                   SUM(s.total_cents)            AS revenue_cents,
                   COUNT(*)                      AS sale_count
            FROM sale_valid s
            LEFT JOIN product p  ON p.id = s.product_id
            LEFT JOIN category c ON c.id = p.category_id
            GROUP BY c.id
            ORDER BY revenue_cents DESC
            """
        )

    def top_products(self, limit: int = 10) -> list[dict[str, Any]]:
        return self.db.query(
            """
            SELECT p.code, p.description, SUM(s.total_cents) AS revenue_cents, SUM(s.quantity) AS units
            FROM sale_valid s JOIN product p ON p.id = s.product_id
            GROUP BY p.id ORDER BY revenue_cents DESC LIMIT ?
            """,
            (limit,),
        )

    def top_customers(self, limit: int = 10) -> list[dict[str, Any]]:
        return self.db.query(
            """
            SELECT customer, SUM(total_cents) AS revenue_cents, COUNT(*) AS sale_count
            FROM sale_valid WHERE customer IS NOT NULL AND customer <> ''
            GROUP BY customer ORDER BY revenue_cents DESC LIMIT ?
            """,
            (limit,),
        )

    def health(self) -> dict[str, Any]:
        """How much of the sales data is usable, and what the excluded rows are worth."""
        rows = self.db.query("SELECT status, COUNT(*) AS n, COALESCE(SUM(total_cents), 0) AS cents FROM sale GROUP BY status")
        return {row["status"]: {"count": row["n"], "cents": row["cents"]} for row in rows}
