"""Finding the supplier and the invoice a person named.

Both are the same problem: someone writes "Cuyo" or "F-7797" and the tool has to land on the
row that exists, or say clearly that it could not. Neither of these ever creates anything.

The supplier side is `ingest`'s resolver, untouched: it matches against the real catalog and
remembers the spelling it resolved, so the same way of writing a name is instant next time.
"""

from __future__ import annotations

from typing import Any

from ingest.resolvers import SupplierResolver
from store import Store

from ..errors import ToolError


class SupplierLookup:
    """A written name to a real supplier. A name that does not resolve is an error, never a new supplier."""

    def __init__(self, store: Store):
        self._store = store
        self._resolver = SupplierResolver(store)

    def resolve(self, spelling: str):
        return self._resolver.resolve(spelling or "")

    def find(self, spelling: str) -> dict[str, Any]:
        supplier_id, match = self._resolver.resolve(spelling or "")
        if supplier_id is None:
            raise ToolError(self._not_found(spelling, match))
        supplier = self._store.suppliers.get(supplier_id)
        if supplier is None:
            raise ToolError(f"El proveedor {spelling!r} figura en el catalogo pero no esta en la base")
        return supplier

    def _not_found(self, spelling: str, match: Any) -> str:
        candidates = ", ".join(str(value) for value, _ in getattr(match, "candidates", ())[:3])
        known = ", ".join(row["name"] for row in self._store.suppliers.all(order_by="name"))
        detail = f" Los que mas se parecen: {candidates}." if candidates else ""
        return (
            f"No pude identificar al proveedor {spelling!r} en el catalogo.{detail} "
            f"Los proveedores cargados son: {known or 'ninguno'}"
        )


class InvoiceLookup:
    """An invoice number, or an id, to the invoice row."""

    def __init__(self, store: Store, suppliers: SupplierLookup):
        self._store = store
        self._suppliers = suppliers

    def find(self, reference: object, supplier_name: str = "") -> dict[str, Any]:
        text = str(reference or "").strip()
        if not text:
            raise ToolError("Falta decir de que factura se trata")

        if supplier_name:
            supplier = self._suppliers.find(supplier_name)
            invoice = self._store.invoices.by_number(supplier["id"], text.upper())
            if invoice is None:
                raise ToolError(f"El proveedor {supplier['name']} no tiene la factura {text.upper()}")
            return invoice

        invoice = self._store.invoices.get_by("number", text.upper())
        if invoice is None and text.isdigit():
            invoice = self._store.invoices.get(int(text))
        if invoice is None:
            raise ToolError(f"No encontre la factura {text.upper()}")
        return invoice
