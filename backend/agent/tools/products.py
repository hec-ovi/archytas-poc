"""Products and what is left of them on the shelf."""

from __future__ import annotations

from typing import Any

from normalizer.text import fold

from .base import Parameter, Tool
from .presenters import money

MAX_ROWS = 40


class ConsultarProductos(Tool):
    name = "consultar_productos"
    parameters = (
        Parameter("buscar", "string"),
        Parameter("stock_maximo", "integer"),
    )

    def run(self, buscar: str = "", stock_maximo: object = None, **_: Any) -> dict[str, Any]:
        rows = self._store.products.stock_snapshot()

        if buscar:
            needle = fold(str(buscar))
            rows = [row for row in rows if needle in fold(f"{row['code']} {row['description']}")]
        if stock_maximo is not None and str(stock_maximo).strip() != "":
            limit = int(stock_maximo)
            rows = [row for row in rows if row["stock"] is not None and row["stock"] <= limit]

        products = [
            {
                "codigo": row["code"],
                "descripcion": row["description"],
                "rubro": row["category"],
                "stock": row["stock"],
                **money(row["price_cents"], "precio"),
            }
            for row in rows[:MAX_ROWS]
        ]
        return {"productos": products, "encontrados": len(rows), "mostrados": len(products)}
