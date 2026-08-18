"""How a database row is handed to the model.

Every amount travels twice: in integer cents, and already written the way the client reads
it. That is deliberate. The model must never divide anything by a hundred, and it must never
be the one deciding how a number is spelled out.

The keys are in Spanish because they end up quoted in the answer the person reads.
"""

from __future__ import annotations

from typing import Any

from ..values import as_money


def money(cents: object, name: str) -> dict[str, Any]:
    """One amount under two keys: `saldo` for reading, `saldo_centavos` for arithmetic."""
    value = int(cents or 0)
    return {name: as_money(value), f"{name}_centavos": value}


def supplier_view(row: dict[str, Any]) -> dict[str, Any]:
    """A row of `supplier_position`: what we bought, paid and still owe."""
    view = {
        "proveedor": row.get("name"),
        "slug": row.get("slug"),
        "cuit": row.get("cuit"),
        "plazo_pactado_dias": row.get("terms_days"),
        "facturas": row.get("invoice_count", 0),
        **money(row.get("purchased_cents"), "comprado"),
        **money(row.get("paid_cents"), "pagado"),
        **money(row.get("owed_cents"), "deuda"),
    }
    overdue = row.get("oldest_overdue_days")
    if overdue is not None and overdue > 0:
        view["atraso_mas_viejo_dias"] = overdue
    return view


def invoice_view(row: dict[str, Any]) -> dict[str, Any]:
    """A row of `invoice_balance`: the invoice with its balance already calculated."""
    view = {
        "id": row.get("id"),
        "numero": row.get("number"),
        "proveedor": row.get("supplier_name"),
        "emitida": row.get("issued_on"),
        "vence": row.get("due_on"),
        **money(row.get("amount_cents"), "total"),
        **money(row.get("paid_cents"), "pagado"),
        **money(row.get("balance_cents"), "saldo"),
        "estado_pago": row.get("payment_state"),
        "tiene_recibo": bool(row.get("has_receipt")),
    }
    overdue = row.get("days_overdue")
    if overdue is not None and overdue > 0 and int(row.get("balance_cents") or 0) > 0:
        view["dias_de_atraso"] = overdue
    return view


def payment_view(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("id"),
        "referencia": row.get("reference"),
        "fecha": row.get("paid_on"),
        **money(row.get("amount_cents"), "monto"),
        "registrado_por": row.get("created_by"),
    }


def receipt_view(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {
        "numero": row.get("number"),
        "emitido": row.get("issued_on"),
        "emitido_por": row.get("issued_by"),
    }
