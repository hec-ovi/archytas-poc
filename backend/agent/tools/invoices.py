"""Invoices: the list by state, one invoice with everything hanging off it, and the receipts
that are still on time.

A question that ends in a subset is answered by a query, never by handing the model a long
list and trusting it to narrow it down. The receipts one is the clearest case: the window to
issue a receipt closes on the due date, so a missed row costs money."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from store import Store

from ..library import PromptLibrary
from .base import Parameter, Tool
from .lookup import InvoiceLookup, SupplierLookup
from .presenters import invoice_view, money, payment_view, receipt_view

STATES = ("impaga", "parcial", "saldada")
DEFAULT_DAYS_AHEAD = 30


class ConsultarFacturas(Tool):
    name = "consultar_facturas"
    section = "facturas"
    parameters = (
        Parameter("estado", "string", enum=STATES),
        Parameter("proveedor", "string"),
        Parameter("solo_vencidas", "boolean"),
    )

    def __init__(self, store: Store, prompts: PromptLibrary, suppliers: SupplierLookup):
        super().__init__(store, prompts)
        self._suppliers = suppliers

    def run(self, estado: str = "", proveedor: str = "", solo_vencidas: object = False,
            **_: Any) -> dict[str, Any]:
        supplier = self._suppliers.find(proveedor) if proveedor else None
        rows = self._store.invoices.listing(
            supplier_id=supplier["id"] if supplier else None,
            state=estado or None,
        )
        invoices = [invoice_view(row) for row in rows]
        if solo_vencidas:
            invoices = [row for row in invoices if row.get("dias_de_atraso")]
        return {
            "facturas": invoices,
            "cantidad": len(invoices),
            **money(sum(row["saldo_centavos"] for row in invoices), "saldo_total"),
            "resumen_por_estado": self._store.invoices.payment_summary(),
        }


class ConsultarFactura(Tool):
    name = "consultar_factura"
    section = "facturas"
    parameters = (
        Parameter("factura", "string", required=True),
        Parameter("proveedor", "string"),
    )

    def __init__(self, store: Store, prompts: PromptLibrary, invoices: InvoiceLookup):
        super().__init__(store, prompts)
        self._invoices = invoices

    def run(self, factura: str = "", proveedor: str = "", **_: Any) -> dict[str, Any]:
        invoice = self._invoices.find(factura, proveedor)
        balance = self._store.invoices.balance(invoice["id"])
        return {
            "factura": invoice_view(balance),
            "pagos": [payment_view(row) for row in self._store.payments.for_invoice(invoice["id"])],
            "recibo": receipt_view(self._store.receipts.for_invoice(invoice["id"])),
        }


class ConsultarRecibosFaltantes(Tool):
    """The invoices whose receipt can still be issued, and for how long.

    The receipt is the proof the invoice was received, and the portal only takes it up to the
    due date. After that it is a conversation with the supplier, so the useful answer is the
    ones still inside the window.
    """

    name = "consultar_recibos_faltantes"
    section = "facturas"
    parameters = (Parameter("dias_adelante", "integer"),)

    def run(self, dias_adelante: object = None, **_: Any) -> dict[str, Any]:
        ahead = int(dias_adelante) if str(dias_adelante or "").strip() else DEFAULT_DAYS_AHEAD
        today = date.today().isoformat()
        limit = (date.today() + timedelta(days=ahead)).isoformat()

        rows = self._store.invoices.without_receipt_due_before(limit)
        inside = [row for row in rows if row["due_on"] >= today]
        expired = len(rows) - len(inside)

        invoices = [
            {**invoice_view(row), "dias_para_vencer": _days_between(today, row["due_on"])}
            for row in inside
        ]
        return {
            "desde": today,
            "hasta": limit,
            "facturas": invoices,
            "cantidad": len(invoices),
            **money(sum(row["saldo_centavos"] for row in invoices), "saldo_total"),
            "ya_vencidas_sin_recibo": expired,
        }


def _days_between(start: str, end: str) -> int:
    return (date.fromisoformat(end) - date.fromisoformat(start)).days
