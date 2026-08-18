"""What we owe: one supplier, or all of them.

The balance is never calculated here. It comes from the `supplier_position` view, which is
the invoices minus the payments actually recorded.
"""

from __future__ import annotations

from typing import Any

from store import Store

from ..errors import ToolError
from ..library import PromptLibrary
from .base import Parameter, Tool
from .lookup import SupplierLookup
from .presenters import money, supplier_view


class ConsultarProveedor(Tool):
    name = "consultar_proveedor"
    parameters = (Parameter("proveedor", "string", required=True),)

    def __init__(self, store: Store, prompts: PromptLibrary, suppliers: SupplierLookup):
        super().__init__(store, prompts)
        self._suppliers = suppliers

    def run(self, proveedor: str = "", **_: Any) -> dict[str, Any]:
        supplier = self._suppliers.find(proveedor)
        position = self._store.suppliers.position(supplier["id"])
        if position is None:
            raise ToolError(f"No hay posicion de cuenta para {supplier['name']}")
        return supplier_view(position)


class ConsultarDeudas(Tool):
    name = "consultar_deudas"

    def run(self, **_: Any) -> dict[str, Any]:
        positions = [supplier_view(row) for row in self._store.suppliers.positions()]
        total = sum(row["deuda_centavos"] for row in positions)
        return {"proveedores": positions, **money(total, "deuda_total")}
