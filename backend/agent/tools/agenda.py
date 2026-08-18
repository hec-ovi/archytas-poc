"""What falls due between two dates."""

from __future__ import annotations

from typing import Any

from .base import Parameter, Tool
from .presenters import money
from ..values import as_date


class ConsultarCalendario(Tool):
    name = "consultar_calendario"
    section = "calendario"
    parameters = (
        Parameter("desde", "string", required=True),
        Parameter("hasta", "string", required=True),
    )

    def run(self, desde: object = None, hasta: object = None, **_: Any) -> dict[str, Any]:
        start, end = as_date(desde, "la fecha desde"), as_date(hasta, "la fecha hasta")
        events = [
            {
                "fecha": row["on_date"],
                "titulo": row["title"],
                "tipo": row["kind"],
                "proveedor": row.get("supplier_name"),
                "factura": row.get("invoice_number"),
                **money(row.get("amount_cents"), "monto"),
                "saldo_centavos": row.get("balance_cents"),
                "estado_pago": row.get("payment_state"),
                "tiene_recibo": bool(row.get("has_receipt")),
                "movido_desde": row.get("moved_from"),
            }
            for row in self._store.calendar.between(start, end)
        ]
        return {
            "desde": start,
            "hasta": end,
            "vencimientos": events,
            **money(sum(event["monto_centavos"] for event in events), "monto_total"),
        }
