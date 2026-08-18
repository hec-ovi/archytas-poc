"""Sales by month. Only the ones that can be counted: the view leaves the duplicates out."""

from __future__ import annotations

from typing import Any

from .base import Parameter, Tool
from .presenters import money


class ConsultarVentas(Tool):
    name = "consultar_ventas"
    parameters = (Parameter("anio", "integer"),)

    def run(self, anio: object = None, **_: Any) -> dict[str, Any]:
        rows = self._store.sales.revenue_by_month()
        if anio:
            prefix = str(anio).strip()
            rows = [row for row in rows if str(row["month"]).startswith(prefix)]

        months = [
            {
                "mes": row["month"],
                "ventas": row["sale_count"],
                "unidades": row["units"],
                **money(row["revenue_cents"], "facturado"),
            }
            for row in rows
        ]
        return {
            "meses": months,
            **money(sum(row["facturado_centavos"] for row in months), "facturado_total"),
            "excluidas": len(self._store.sales.excluded()),
        }
