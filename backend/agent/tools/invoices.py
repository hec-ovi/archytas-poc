"""Invoices: the list by state, and one invoice with everything hanging off it."""

from __future__ import annotations

from typing import Any

from store import Store

from ..library import PromptLibrary
from .base import Parameter, Tool
from .lookup import InvoiceLookup, SupplierLookup
from .presenters import invoice_view, money, payment_view, receipt_view

STATES = ("impaga", "parcial", "saldada")


class ConsultarFacturas(Tool):
    name = "consultar_facturas"
    parameters = (
        Parameter("estado", "string", enum=STATES),
        Parameter("proveedor", "string"),
    )

    def __init__(self, store: Store, prompts: PromptLibrary, suppliers: SupplierLookup):
        super().__init__(store, prompts)
        self._suppliers = suppliers

    def run(self, estado: str = "", proveedor: str = "", **_: Any) -> dict[str, Any]:
        supplier = self._suppliers.find(proveedor) if proveedor else None
        rows = self._store.invoices.listing(
            supplier_id=supplier["id"] if supplier else None,
            state=estado or None,
        )
        invoices = [invoice_view(row) for row in rows]
        return {
            "facturas": invoices,
            "cantidad": len(invoices),
            **money(sum(row["saldo_centavos"] for row in invoices), "saldo_total"),
            "resumen_por_estado": self._store.invoices.payment_summary(),
        }


class ConsultarFactura(Tool):
    name = "consultar_factura"
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
