"""Loading rubros, products, price history and the daily stock reading.

Three things happen here that the portal cannot do on its own:

- the real rubros are discovered from the spellings, and a product with no rubro is placed
  by its subcategory instead of being dropped in a leftovers pile
- price history comes from the per-article detail route, which is the only place the portal
  keeps it and is not linked from any menu
- stock has no history anywhere, so a reading is taken each pass. Without this, "what
  happened with stock" has no answer, ever.
"""

from __future__ import annotations

from datetime import date

from ingest.report import StageReport
from ingest.resolvers import CategoryResolver
from ingest.review_queue import ReviewQueue
from normalizer.money import parse_amount
from store import Store

# The catalogue only exists from the day we start looking, so the first reading is dated
# where the portal's own price history starts. Otherwise every product looks new on day one.
HISTORY_START = "2023-01-01"


class ProductStage:
    name = "productos"

    def __init__(self, store: Store, categories: CategoryResolver, review: ReviewQueue):
        self._store = store
        self._categories = categories
        self._review = review

    def run(self, rows: list[dict], report: StageReport, history: dict[str, list[dict]] | None = None) -> None:
        report.seen = len(rows)
        today = date.today().isoformat()
        first_pass = self._store.products.count() == 0

        discovery = self._categories.discover([row.get("categoria", "") for row in rows])
        report.note(f"{discovery['escrituras']} escrituras de rubro agrupadas en {discovery['rubros']} rubros reales")

        unplaced: list[tuple[dict, object]] = []
        for row in rows:
            category_id, match = self._categories.resolve(row.get("categoria", ""), row.get("subcategoria", ""))
            if category_id is None:
                # held back rather than raised now: the second look below places most of
                # these, and an item that resolves itself should never reach a person
                unplaced.append((row, match))
            else:
                report.resolved += 1

            price = parse_amount(row.get("precio"))
            stock = _as_int(row.get("stock"))
            existing = self._store.products.by_external(row["id"])

            values = {
                "external_id": row["id"],
                "code": row.get("codigo", ""),
                "description": row.get("descripcion", ""),
                "category_id": category_id,
                "subcategory": row.get("subcategoria"),
                "price_cents": price.value,
                "stock": stock,
                "last_seen": today,
            }
            # first_seen is written once and never touched: it is the only thing that can
            # answer "which products are new", since the portal carries no creation date
            if existing is None:
                values["first_seen"] = HISTORY_START if first_pass else today
            product_id = self._store.products.save(values)
            report.stored += 1

            self._store.prices.record(product_id, today, price.value, stock, source="lectura-diaria")
            for point in (history or {}).get(row["id"], []):
                point_price = parse_amount(point.get("precio"))
                if point.get("fecha") and point_price.value is not None:
                    self._store.prices.record(product_id, point["fecha"], point_price.value, None, source="portal")

        # a product with a blank rubro is placed by its subcategory, which needs other
        # products with that subcategory already loaded. The first one processed has nobody
        # to learn from, so the leftovers get a second look once everything is in.
        for product in self._store.products.without_category():
            category_id, _ = self._categories.resolve("", product.get("subcategory") or "")
            if category_id:
                self._store.products.update(product["id"], {"category_id": category_id})
                report.resolved += 1

        still_missing = {p["external_id"] for p in self._store.products.without_category()}
        for row, match in unplaced:
            if row["id"] not in still_missing:
                continue
            report.for_review += 1
            self._review.unresolved_value(
                kind="rubro",
                title=f"Rubro sin resolver en {row.get('codigo')}",
                detail=f"El producto {row.get('codigo')} tiene el rubro escrito como {row.get('categoria')!r} "
                       f"y su subrubro no alcanza para ubicarlo",
                raw=row,
                result=match,
            )

        without = len(self._store.products.without_category())
        if without:
            report.note(f"{without} productos siguen sin rubro y estan a la vista, no escondidos en un cajon")
        else:
            report.note("todos los productos quedaron con rubro: los que venian en blanco se ubicaron por su subrubro")


class CatalogImageStage:
    """The picture the portal shows for a product.

    The images are per rubro, not per product: twenty catalogue items share ten pictures
    named after the subcategory. Stored as what it is, an illustration of the rubro.
    """

    name = "imagenes"

    def __init__(self, store: Store):
        self._store = store

    def run(self, rows: list[dict], report: StageReport) -> None:
        report.seen = len(rows)
        for row in rows:
            product = self._store.products.by_external(row["id"])
            if product is None:
                report.skipped += 1
                continue
            self._store.products.update(product["id"], {"image_url": row.get("imagen")})
            report.stored += 1
        report.note("las imagenes son por rubro, no por producto: el portal repite la misma foto para todo el rubro")


def _as_int(value) -> int | None:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None
