"""Suppliers and every way their name has been written.

The client's question is "how many suppliers do I actually have". The portal answers with 25
different strings for 8 companies, and the only place a CUIT appears is the account
statements, so the name is the only bridge between datasets. That makes the alias table the
load-bearing part of this file: once a spelling is resolved, it never has to be resolved
again.
"""

from __future__ import annotations

from typing import Any

from .base import Repository, decode, decode_all


class SupplierRepository(Repository):
    table = "supplier"

    def by_slug(self, slug: str) -> dict[str, Any] | None:
        return self.get_by("slug", slug)

    def by_cuit(self, cuit: str) -> dict[str, Any] | None:
        return self.get_by("cuit", cuit)

    def save(self, values: dict[str, Any]) -> int:
        return self.upsert(values, ["slug"])

    def positions(self) -> list[dict[str, Any]]:
        """What we bought, paid and still owe each supplier, and how old the oldest debt is."""
        return self.db.query("SELECT * FROM supplier_position ORDER BY owed_cents DESC")

    def position(self, supplier_id: int) -> dict[str, Any] | None:
        return self.db.one("SELECT * FROM supplier_position WHERE supplier_id = ?", (supplier_id,))

    def with_terms_compliance(self) -> list[dict[str, Any]]:
        """Are we paying on the terms we agreed, or later?

        Comparing the agreed term against the due date the invoice actually carries is the
        only way to see whether the arrangement is being honoured.
        """
        return self.db.query(
            """
            SELECT
                s.id AS supplier_id,
                s.name,
                s.terms_days,
                COUNT(i.id) AS invoice_count,
                SUM(CASE
                        WHEN s.terms_days IS NOT NULL
                         AND CAST(julianday(i.due_on) - julianday(i.issued_on) AS INTEGER) = s.terms_days
                        THEN 1 ELSE 0
                    END) AS on_terms_count
            FROM supplier s
            LEFT JOIN invoice i ON i.supplier_id = s.id AND i.issued_on IS NOT NULL AND i.due_on IS NOT NULL
            GROUP BY s.id
            ORDER BY s.name
            """
        )


class SupplierAliasRepository(Repository):
    table = "supplier_alias"

    def resolve(self, spelling: str) -> dict[str, Any] | None:
        return self.get_by("spelling", spelling)

    def remember(self, supplier_id: int, spelling: str, method: str, confidence: float = 1.0) -> int:
        return self.upsert(
            {
                "supplier_id": supplier_id,
                "spelling": spelling,
                "method": method,
                "confidence": confidence,
            },
            ["spelling"],
        )

    def for_supplier(self, supplier_id: int) -> list[dict[str, Any]]:
        return decode_all(
            self.db.query("SELECT * FROM supplier_alias WHERE supplier_id = ? ORDER BY spelling", (supplier_id,))
        )

    def catalog_rows(self) -> list[dict[str, Any]]:
        """Every supplier with its known spellings, ready to build a matcher from."""
        return self.db.query(
            """
            SELECT s.id, s.slug, s.name, GROUP_CONCAT(a.spelling, CHAR(31)) AS spellings
            FROM supplier s
            LEFT JOIN supplier_alias a ON a.supplier_id = s.id
            GROUP BY s.id
            """
        )
