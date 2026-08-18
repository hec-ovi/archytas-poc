"""Loading the inbox.

Four kinds of message arrive and the portal labels none of them: the kind is hidden in the
id prefix. Supplier claims are the ones that cost money when ignored, so they are kept apart
from the system's own warnings rather than piled together.

Two of the prefixes are both claims. `msg-reclamo` is a supplier writing in; `msg-auto` is
the same thing regenerated daily for whatever is most overdue, which is why a new one shows
up every morning. Both are a supplier asking for money.

Stock warnings name their article in the subject line and nowhere else, so the code is read
from there to link the product.
"""

from __future__ import annotations

import re

from ingest.report import StageReport
from ingest.resolvers import SupplierResolver
from normalizer.dates import parse_date
from store import Store

# the prefix in the message id is the only thing that says what a message is
KINDS = {
    "msg-venc": "vencimiento",     # the portal warning that something is about to fall due
    "msg-stock": "stock",          # the portal warning that an article is running low
    "msg-reclamo": "reclamo",      # a supplier writing to ask for money
    "msg-auto": "reclamo",         # the same claim, regenerated every day for the worst debt
}

# "Stock bajo - COR-0060"
PRODUCT_CODE = re.compile(r"\b(COR-\d{3,})\b")


class MessageStage:
    name = "mensajes"

    def __init__(self, store: Store, suppliers: SupplierResolver):
        self._store = store
        self._suppliers = suppliers

    def run(self, rows: list[dict], report: StageReport) -> None:
        report.seen = len(rows)
        for row in rows:
            kind = next((v for prefix, v in KINDS.items() if str(row.get("id", "")).startswith(prefix)), "reclamo")

            sender = row.get("remitente", "")
            supplier_id = None
            if self._suppliers.is_supplier(sender):
                supplier_id, _ = self._suppliers.resolve(sender)

            invoice = self._store.invoices.by_external(row.get("factura_id") or "")
            product = None
            if invoice is None:
                code = PRODUCT_CODE.search(f"{row.get('asunto', '')} {row.get('cuerpo', '')}")
                if code:
                    product = self._store.products.get_by("code", code.group(1))

            self._store.messages.save(
                {
                    "external_id": row["id"],
                    "received_on": parse_date(row.get("fecha")).value,
                    "sender": sender,
                    "supplier_id": supplier_id,
                    "subject": row.get("asunto", ""),
                    "body": row.get("cuerpo", ""),
                    "invoice_id": invoice["id"] if invoice else None,
                    "product_id": product["id"] if product else None,
                    "kind": kind,
                    "resolved": 0,
                    "extra": {"leido_en_el_portal": bool(row.get("leido"))},
                }
            )
            report.stored += 1

        report.note("leido en el portal no es lo mismo que resuelto: un mensaje sigue abierto hasta que alguien lo cierra aca")
