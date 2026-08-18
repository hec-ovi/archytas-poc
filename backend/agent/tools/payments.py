"""The three changes to an invoice, with the same rules the rest of the system enforces.

A payment cannot be bigger than what is owed. A receipt cannot be issued once the invoice
has expired, because the portal stops accepting it and past that date it is a conversation
with the supplier, not a button. An amount only changes with a reason attached.

Every one of them writes down who asked for it. An amount that changes with nobody's name on
it is how trust in a system dies.
"""

from __future__ import annotations

from typing import Any

from store import Store

from ..errors import ToolError
from ..library import PromptLibrary
from ..values import as_cents, as_date, as_money, today
from .base import Parameter, Tool
from .lookup import InvoiceLookup
from .presenters import invoice_view, money, payment_view, receipt_view

MIN_REASON = 3


class InvoiceWriteTool(Tool):
    """Shared ground: find the invoice, and refuse to write for nobody."""

    needs_user = True
    section = "facturas"

    def __init__(self, store: Store, prompts: PromptLibrary, invoices: InvoiceLookup):
        super().__init__(store, prompts)
        self._invoices = invoices

    def _target(self, factura: object, proveedor: str, usuario: str) -> dict[str, Any]:
        if not usuario:
            raise ToolError("No puedo registrar un cambio sin saber quien lo pide")
        return self._invoices.find(factura, proveedor)


class RegistrarPago(InvoiceWriteTool):
    name = "registrar_pago"
    parameters = (
        Parameter("factura", "string", required=True),
        Parameter("monto_centavos", "integer", required=True),
        Parameter("fecha", "string"),
        Parameter("referencia", "string"),
        Parameter("proveedor", "string"),
    )

    def run(self, factura: object = None, monto_centavos: object = None, fecha: object = None,
            referencia: str = "", proveedor: str = "", usuario: str = "", **_: Any) -> dict[str, Any]:
        invoice = self._target(factura, proveedor, usuario)
        amount = as_cents(monto_centavos, "el monto del pago")
        if amount <= 0:
            raise ToolError("El pago tiene que ser mayor a cero")

        balance = self._store.invoices.balance(invoice["id"])
        if amount > balance["balance_cents"]:
            raise ToolError(
                f"El pago de {as_money(amount)} supera el saldo de {as_money(balance['balance_cents'])} "
                f"de la factura {invoice['number']}"
            )

        paid_on = as_date(fecha, "la fecha del pago") if fecha else today()
        self._store.payments.insert(
            {
                "reference": referencia or f"PAGO-{invoice['number']}-{paid_on}",
                "invoice_id": invoice["id"],
                "supplier_id": invoice.get("supplier_id"),
                "paid_on": paid_on,
                "amount_cents": amount,
                "created_by": usuario,
                "extra": {"origen": "agente", "pedido_por": usuario},
            }
        )

        updated = self._store.invoices.balance(invoice["id"])
        return {
            "registrado": True,
            **money(amount, "pago"),
            "fecha": paid_on,
            "factura": invoice_view(updated),
            "pagos": [payment_view(row) for row in self._store.payments.for_invoice(invoice["id"])],
        }


class EmitirRecibo(InvoiceWriteTool):
    name = "emitir_recibo"
    parameters = (
        Parameter("factura", "string", required=True),
        Parameter("proveedor", "string"),
    )

    def run(self, factura: object = None, proveedor: str = "", usuario: str = "", **_: Any) -> dict[str, Any]:
        invoice = self._target(factura, proveedor, usuario)

        existing = self._store.receipts.for_invoice(invoice["id"])
        if existing:
            return {"emitido": False, "motivo": "la factura ya tenia recibo", "recibo": receipt_view(existing)}

        issued_on = today()
        if invoice.get("due_on") and issued_on > invoice["due_on"]:
            raise ToolError(
                f"La factura {invoice['number']} vencio el {invoice['due_on']} y el recibo se emite hasta la "
                f"fecha de vencimiento. Hay que arreglarlo con el proveedor."
            )

        self._store.receipts.save(
            {
                "number": self._store.receipts.number_for(invoice["number"]),
                "invoice_id": invoice["id"],
                "issued_on": issued_on,
                "issued_by": usuario,
                "extra": {"origen": "agente", "pedido_por": usuario},
            }
        )
        return {"emitido": True, "recibo": receipt_view(self._store.receipts.for_invoice(invoice["id"]))}


class AjustarMonto(InvoiceWriteTool):
    name = "ajustar_monto"
    parameters = (
        Parameter("factura", "string", required=True),
        Parameter("monto_centavos", "integer", required=True),
        Parameter("motivo", "string", required=True),
        Parameter("proveedor", "string"),
    )

    def run(self, factura: object = None, monto_centavos: object = None, motivo: str = "",
            proveedor: str = "", usuario: str = "", **_: Any) -> dict[str, Any]:
        invoice = self._target(factura, proveedor, usuario)
        amount = as_cents(monto_centavos, "el monto nuevo")
        if amount < 0:
            raise ToolError("El monto de una factura no puede ser negativo")
        if len(motivo.strip()) < MIN_REASON:
            raise ToolError("Hace falta un motivo para cambiar el monto de una factura")

        history = list(invoice.get("extra", {}).get("ajustes", []))
        history.append(
            {
                "de": invoice["amount_cents"],
                "a": amount,
                "motivo": motivo.strip(),
                "por": usuario,
                "cuando": today(),
                "origen": "agente",
            }
        )
        self._store.invoices.update(
            invoice["id"],
            {"amount_cents": amount, "extra": {**invoice.get("extra", {}), "ajustes": history}},
        )
        return {
            "ajustado": True,
            **money(invoice["amount_cents"], "monto_anterior"),
            **money(amount, "monto_nuevo"),
            "motivo": motivo.strip(),
            "factura": invoice_view(self._store.invoices.balance(invoice["id"])),
        }
