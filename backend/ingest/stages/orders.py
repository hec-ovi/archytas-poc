"""Loading purchase orders.

The client's problem is not the order, it is the silence after it: nobody follows up, and
things get ordered twice. So the order's state is normalized into words that mean something
when you sort by them, and the age of an open order is what the screen leads with.
"""

from __future__ import annotations

from ingest.report import StageReport
from ingest.resolvers import SupplierResolver
from ingest.review_queue import ReviewQueue
from normalizer.dates import parse_date
from normalizer.money import parse_amount
from normalizer.text import fold
from store import Store

# what the portal writes, and the short state we sort and count by
STATES = {
    "pendiente de envio": "por-enviar",
    "enviada al proveedor": "enviada",
    "pendiente de confirmacion": "pendiente",
    "confirmada por proveedor": "confirmada",
    "recibida": "recibida",
    "recibida parcial": "recibida-parcial",
    "anulada": "anulada",
}


class PurchaseOrderStage:
    name = "ordenes de compra"

    def __init__(self, store: Store, suppliers: SupplierResolver, review: ReviewQueue):
        self._store = store
        self._suppliers = suppliers
        self._review = review

    def run(self, rows: list[dict], report: StageReport) -> None:
        report.seen = len(rows)
        seen_states: set[str] = set()
        for row in rows:
            raw_name = row.get("proveedor", "")
            supplier_id, match = self._suppliers.resolve(raw_name)
            if supplier_id is None:
                report.for_review += 1
                self._review.unresolved_value(
                    kind="proveedor",
                    title=f"Proveedor sin identificar en la orden {row.get('numero')}",
                    detail=f"La orden {row.get('numero')} figura a nombre de {raw_name!r}",
                    raw=row,
                    result=match,
                )
            else:
                report.resolved += 1

            raw_state = (row.get("estado") or "").strip()
            state = STATES.get(fold(raw_state), fold(raw_state).replace(" ", "-") or "sin-estado")
            seen_states.add(raw_state)
            product = self._store.products.by_external(row.get("productoId") or "")

            self._store.orders.save(
                {
                    "external_id": row["id"],
                    "number": row.get("numero", ""),
                    "supplier_id": supplier_id,
                    "product_id": product["id"] if product else None,
                    "ordered_on": parse_date(row.get("fecha")).value,
                    "quantity": row.get("cantidad"),
                    "estimated_cents": parse_amount(row.get("montoEstimado")).value,
                    "status": state,
                    "status_raw": raw_state,
                    "extra": {"texto_producto": row.get("productoTexto")},
                }
            )
            report.stored += 1

        unknown = [s for s in seen_states if fold(s) not in STATES]
        if unknown:
            report.note(f"estados que el portal usa y no estaban previstos: {', '.join(sorted(unknown))}")
