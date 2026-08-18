"""The purchase orders nobody followed up on.

"I end up ordering the same thing twice because nobody remembered the first order." So the
question is not the list of orders, it is the ones that have been open too long. How long is
a setting the client changes himself, so the default comes from the database, not from here.
"""

from __future__ import annotations

from typing import Any

from .base import Parameter, Tool
from .presenters import money


class ConsultarOrdenesOlvidadas(Tool):
    name = "consultar_ordenes_olvidadas"
    section = "ordenes"
    parameters = (Parameter("dias", "integer"),)

    def run(self, dias: object = None, **_: Any) -> dict[str, Any]:
        limit = int(dias) if str(dias or "").strip() else int(self._store.settings.get_value("orden_vieja_dias", 30))
        orders = [
            {
                "numero": row["number"],
                "proveedor": row.get("supplier_name"),
                "pedida": row["ordered_on"],
                "dias_esperando": row.get("age_days"),
                "estado": row["status"],
                "cantidad": row["quantity"],
                **money(row.get("estimated_cents"), "estimado"),
            }
            for row in self._store.orders.stale(limit)
        ]
        return {
            "dias_para_olvidada": limit,
            "ordenes": orders,
            "cantidad": len(orders),
            **money(sum(row["estimado_centavos"] for row in orders), "estimado_total"),
        }
