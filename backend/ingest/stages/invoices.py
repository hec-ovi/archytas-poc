"""Loading invoices, the payments against them, and which ones already have a receipt.

Two fields the portal publishes are deliberately ignored.

`diasVencida` is recomputed by the portal on every request against the current date, so a
stored copy is wrong the next morning. It is derived here instead.

`pagado` and `saldo` are the portal's own arithmetic. They happen to agree with the payments
today, but a total that is stored rather than summed is a total that can drift away from the
payments underneath it. The balance comes from the payments, always.
"""

from __future__ import annotations

from ingest.report import StageReport
from ingest.resolvers import SupplierResolver
from ingest.review_queue import ReviewQueue
from normalizer.dates import parse_date
from normalizer.money import parse_amount
from store import Store


class InvoiceStage:
    name = "facturas"

    # what the portal calls the file it holds, mapped to how we parse that file later.
    # 46 of the 100 invoices are photos of paper, so getting this label right is what tells
    # the screen (and whoever opens it) that reading it needs OCR.
    SOURCE_KINDS = {
        "Excel": "excel",
        "PDF": "pdf",
        "PDF (escaneado)": "pdf-escaneado",
    }

    def __init__(self, store: Store, suppliers: SupplierResolver, review: ReviewQueue):
        self._store = store
        self._suppliers = suppliers
        self._review = review

    def run(self, rows: list[dict], report: StageReport) -> None:
        report.seen = len(rows)
        for row in rows:
            raw_name = row.get("proveedor", "")
            supplier_id, match = self._suppliers.resolve(raw_name)
            if supplier_id is None:
                report.for_review += 1
                self._review.unresolved_value(
                    kind="proveedor",
                    title=f"Proveedor sin identificar en la factura {row.get('numero')}",
                    detail=f"La factura {row.get('numero')} vino a nombre de {raw_name!r} y no coincide con ningun proveedor conocido",
                    raw=row,
                    result=match,
                )
            else:
                report.resolved += 1

            issued = parse_date(row.get("fecha"))
            due = parse_date(row.get("vencimiento"))
            amount = parse_amount(row.get("monto"))
            product = self._store.products.by_external(row.get("productoId") or "")

            invoice_id = self._store.invoices.save(
                {
                    "external_id": row["id"],
                    "number": row.get("numero", ""),
                    "supplier_id": supplier_id,
                    "product_id": product["id"] if product else None,
                    "issued_on": issued.value,
                    "due_on": due.value,
                    "amount_cents": amount.value or 0,
                    "source_kind": self._source_kind(row.get("tipo", ""), report),
                    "status": "vigente" if supplier_id else "en-revision",
                    "extra": {"tipo_archivo": row.get("tipo"), "texto_producto": row.get("productoTexto")},
                }
            )
            report.stored += 1

            # the portal only says yes or no, so the receipt is recorded as issued without a
            # date it never published
            if row.get("reciboGenerado"):
                self._store.receipts.save(
                    {
                        "number": self._store.receipts.number_for(row.get("numero", str(invoice_id))),
                        "invoice_id": invoice_id,
                        "issued_on": due.value or issued.value or "",
                        "issued_by": "portal",
                        "extra": {"origen": "el portal ya lo tenia emitido"},
                    }
                )

            supplier = self._store.suppliers.get(supplier_id) if supplier_id else None
            self._store.calendar.sync_from_invoice(
                {"id": invoice_id, "number": row.get("numero", ""), "due_on": due.value, "amount_cents": amount.value},
                supplier["id"] if supplier else None,
            )

        report.note("los dias de atraso no se guardan: cambian solos todas las noches y se calculan al leer")

    def _source_kind(self, raw: str, report: StageReport) -> str:
        """A file format we do not know about is worth saying out loud, not swallowing."""
        known = self.SOURCE_KINDS.get(raw.strip())
        if known:
            return known
        if raw.strip():
            report.note(f"tipo de archivo que el portal usa y no estaba previsto: {raw!r}")
        return "portal"


class PaymentStage:
    """Payments on account. One invoice can have several, and the balance is their sum."""

    name = "pagos"

    def __init__(self, store: Store, suppliers: SupplierResolver, review: ReviewQueue):
        self._store = store
        self._suppliers = suppliers
        self._review = review

    def run(self, rows: list[dict], report: StageReport) -> None:
        report.seen = len(rows)
        for row in rows:
            invoice = self._store.invoices.by_external(row.get("facturaId") or "")
            if invoice is None:
                report.skipped += 1
                report.note(f"el pago {row.get('referencia')} apunta a una factura que no esta")
                continue

            supplier_id, _ = self._suppliers.resolve(row.get("proveedor", ""))
            paid = parse_amount(row.get("monto"))
            self._store.payments.save(
                {
                    "external_id": row["id"],
                    "reference": row.get("referencia", ""),
                    "invoice_id": invoice["id"],
                    "supplier_id": supplier_id or invoice.get("supplier_id"),
                    "paid_on": parse_date(row.get("fecha")).value,
                    "amount_cents": paid.value or 0,
                    "created_by": "portal",
                }
            )
            report.stored += 1
            report.resolved += 1

        summary = self._store.invoices.payment_summary()
        report.note(
            f"saldadas {summary.get('saldada', 0)}, a medias {summary.get('parcial', 0)}, "
            f"sin tocar {summary.get('impaga', 0)}"
        )
