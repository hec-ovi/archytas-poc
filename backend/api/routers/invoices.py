"""Invoices, and the three things the client wanted to do himself.

"Today we do everything by hand: putting together a receipt for a supplier, recording that
we paid something, adjusting an amount. We want to be able to do those things ourselves from
one place, without asking anyone to edit a file for us."

So: register a payment, issue a receipt, adjust an amount. Every one of them writes who did
it and when, because an amount that changes with nobody's name on it is how trust in a
system dies.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from normalizer.money import format_amount
from store import Store

from ..deps import get_hub, get_store
from ..realtime import Hub
from ..security import requires

router = APIRouter(prefix="/api/facturas", tags=["facturas"])


class NewPayment(BaseModel):
    monto_centavos: int = Field(gt=0, description="Monto en centavos")
    fecha: str | None = None
    referencia: str = ""


class AmountAdjustment(BaseModel):
    monto_centavos: int = Field(ge=0)
    motivo: str = Field(min_length=3, description="Por que se ajusta")


@router.get("")
def listing(estado: str | None = None, proveedor: int | None = None,
            store: Store = Depends(get_store), user: dict = Depends(requires("facturas"))) -> dict:
    return {
        "facturas": store.invoices.listing(supplier_id=proveedor, state=estado),
        "resumen": store.invoices.payment_summary(),
    }


@router.get("/{invoice_id}")
def detail(invoice_id: int, store: Store = Depends(get_store),
           user: dict = Depends(requires("facturas"))) -> dict:
    balance = store.invoices.balance(invoice_id)
    if balance is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No existe esa factura")
    return {
        "factura": balance,
        "pagos": store.payments.for_invoice(invoice_id),
        "recibo": store.receipts.for_invoice(invoice_id),
        "cruda": store.invoices.get(invoice_id),
    }


@router.post("/{invoice_id}/pagos", status_code=status.HTTP_201_CREATED)
async def register_payment(invoice_id: int, body: NewPayment, store: Store = Depends(get_store),
                           hub: Hub = Depends(get_hub), user: dict = Depends(requires("facturas"))) -> dict:
    invoice = store.invoices.get(invoice_id)
    if invoice is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No existe esa factura")

    balance = store.invoices.balance(invoice_id)
    if body.monto_centavos > balance["balance_cents"]:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"El pago de {format_amount(body.monto_centavos)} supera el saldo de "
            f"{format_amount(balance['balance_cents'])}",
        )

    store.payments.insert(
        {
            "reference": body.referencia or f"PAGO-{invoice['number']}-{date.today().isoformat()}",
            "invoice_id": invoice_id,
            "supplier_id": invoice.get("supplier_id"),
            "paid_on": body.fecha or date.today().isoformat(),
            "amount_cents": body.monto_centavos,
            "created_by": user["usuario"],
        }
    )
    updated = store.invoices.balance(invoice_id)
    await hub.broadcast("factura-actualizada", {"id": invoice_id, "estado": updated["payment_state"]})
    return {"factura": updated, "pagos": store.payments.for_invoice(invoice_id)}


@router.post("/{invoice_id}/recibo", status_code=status.HTTP_201_CREATED)
async def issue_receipt(invoice_id: int, store: Store = Depends(get_store), hub: Hub = Depends(get_hub),
                        user: dict = Depends(requires("facturas"))) -> dict:
    invoice = store.invoices.get(invoice_id)
    if invoice is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No existe esa factura")

    existing = store.receipts.for_invoice(invoice_id)
    if existing:
        return {"recibo": existing, "nuevo": False}

    # the receipt is the proof the invoice was received and will be paid, and the portal
    # only accepts it up to the due date. Past that, it is a conversation with the supplier,
    # not a button.
    today = date.today().isoformat()
    if invoice.get("due_on") and today > invoice["due_on"]:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"La factura {invoice['number']} vencio el {invoice['due_on']} y el recibo se emite "
            f"hasta la fecha de vencimiento. Hay que arreglarlo con el proveedor.",
        )

    store.receipts.save(
        {
            "number": store.receipts.number_for(invoice["number"]),
            "invoice_id": invoice_id,
            "issued_on": today,
            "issued_by": user["usuario"],
        }
    )
    await hub.broadcast("recibo-emitido", {"factura_id": invoice_id})
    return {"recibo": store.receipts.for_invoice(invoice_id), "nuevo": True}


@router.patch("/{invoice_id}")
async def adjust_amount(invoice_id: int, body: AmountAdjustment, store: Store = Depends(get_store),
                        hub: Hub = Depends(get_hub), user: dict = Depends(requires("facturas"))) -> dict:
    invoice = store.invoices.get(invoice_id)
    if invoice is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No existe esa factura")

    history = invoice.get("extra", {}).get("ajustes", [])
    history.append(
        {
            "de": invoice["amount_cents"],
            "a": body.monto_centavos,
            "motivo": body.motivo,
            "por": user["usuario"],
            "cuando": date.today().isoformat(),
        }
    )
    store.invoices.update(invoice_id, {"amount_cents": body.monto_centavos, "extra": {**invoice.get("extra", {}), "ajustes": history}})
    updated = store.invoices.balance(invoice_id)
    await hub.broadcast("factura-actualizada", {"id": invoice_id, "estado": updated["payment_state"]})
    return {"factura": updated, "ajustes": history}
