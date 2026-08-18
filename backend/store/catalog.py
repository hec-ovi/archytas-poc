"""Products, the rubros they belong to, and how their price moved.

Rubros were typed freely for years, so `category_alias` maps each spelling to the real one.
Price history comes from the portal's per-article detail route; stock has no history
anywhere, so it only exists as a daily snapshot from the moment we start taking them.
"""

from __future__ import annotations

from typing import Any

from .base import Repository, decode_all


class CategoryRepository(Repository):
    table = "category"

    def save(self, values: dict[str, Any]) -> int:
        return self.upsert(values, ["slug"])

    def spend_by_category(self) -> list[dict[str, Any]]:
        """What we spend on each rubro. Products with no rubro are shown, never hidden."""
        return self.db.query(
            """
            SELECT
                COALESCE(c.name, 'Sin rubro')      AS category,
                COALESCE(c.slug, 'sin-rubro')      AS slug,
                COUNT(DISTINCT p.id)               AS product_count,
                COALESCE(SUM(i.amount_cents), 0)   AS purchased_cents
            FROM product p
            LEFT JOIN category c ON c.id = p.category_id
            LEFT JOIN invoice i  ON i.product_id = p.id AND i.status <> 'anulada'
            GROUP BY c.id
            ORDER BY purchased_cents DESC
            """
        )


class CategoryAliasRepository(Repository):
    table = "category_alias"

    def remember(self, category_id: int, spelling: str, method: str, confidence: float = 1.0) -> int:
        return self.upsert(
            {"category_id": category_id, "spelling": spelling, "method": method, "confidence": confidence},
            ["spelling"],
        )

    def catalog_rows(self) -> list[dict[str, Any]]:
        return self.db.query(
            """
            SELECT c.id, c.slug, c.name, GROUP_CONCAT(a.spelling, CHAR(31)) AS spellings
            FROM category c
            LEFT JOIN category_alias a ON a.category_id = c.id
            GROUP BY c.id
            """
        )


class ProductRepository(Repository):
    table = "product"

    def by_external(self, external_id: str) -> dict[str, Any] | None:
        return self.get_by("external_id", external_id)

    def save(self, values: dict[str, Any]) -> int:
        return self.upsert(values, ["external_id"])

    def listing(self) -> list[dict[str, Any]]:
        return decode_all(
            self.db.query(
                """
                SELECT p.*, c.name AS category_name, c.slug AS category_slug
                FROM product p
                LEFT JOIN category c ON c.id = p.category_id
                ORDER BY p.code
                """
            )
        )

    def new_since(self, since: str) -> list[dict[str, Any]]:
        """Products first seen after a date.

        The portal carries no creation date, so "new" can only mean "was not here the last
        time we looked". That is why `first_seen` is written on the first sync and never
        touched again.
        """
        return decode_all(
            self.db.query("SELECT * FROM product WHERE first_seen >= ? ORDER BY first_seen DESC, code", (since,))
        )

    def without_category(self) -> list[dict[str, Any]]:
        return decode_all(self.db.query("SELECT * FROM product WHERE category_id IS NULL ORDER BY code"))

    def stock_snapshot(self) -> list[dict[str, Any]]:
        return self.db.query(
            """
            SELECT p.id, p.code, p.description, p.stock, p.price_cents,
                   COALESCE(c.name, 'Sin rubro') AS category
            FROM product p
            LEFT JOIN category c ON c.id = p.category_id
            ORDER BY p.stock ASC
            """
        )


class PriceHistoryRepository(Repository):
    table = "price_snapshot"

    def record(self, product_id: int, taken_on: str, price_cents: int | None,
               stock: int | None = None, source: str = "portal") -> int:
        return self.upsert(
            {
                "product_id": product_id,
                "taken_on": taken_on,
                "price_cents": price_cents,
                "stock": stock,
                "source": source,
            },
            ["product_id", "taken_on", "source"],
        )

    def for_product(self, product_id: int) -> list[dict[str, Any]]:
        return self.db.query(
            "SELECT taken_on, price_cents, stock, source FROM price_snapshot "
            "WHERE product_id = ? ORDER BY taken_on",
            (product_id,),
        )

    def average_by_month(self) -> list[dict[str, Any]]:
        """How prices moved overall, month by month.

        A price only appears in history on the day it changed, so averaging the rows of each
        month averages whatever handful of articles happened to move that month. That chart
        swings wildly and means nothing. What the client is asking is "how expensive is the
        catalogue now compared to before", so each month takes the last known price of every
        article as of that month, carried forward from whenever it was last set.
        """
        return self.db.query(
            """
            WITH months AS (
                SELECT DISTINCT substr(taken_on, 1, 7) AS month FROM price_snapshot
            ),
            vigente AS (
                SELECT m.month,
                       p.id AS product_id,
                       (SELECT s.price_cents
                          FROM price_snapshot s
                         WHERE s.product_id = p.id
                           AND s.price_cents IS NOT NULL
                           AND substr(s.taken_on, 1, 7) <= m.month
                         ORDER BY s.taken_on DESC
                         LIMIT 1) AS price_cents
                  FROM months m CROSS JOIN product p
            )
            SELECT month,
                   COUNT(price_cents)                  AS products,
                   CAST(AVG(price_cents) AS INTEGER)   AS average_cents
            FROM vigente
            WHERE price_cents IS NOT NULL
            GROUP BY month
            ORDER BY month
            """
        )
