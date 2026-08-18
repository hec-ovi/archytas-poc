"""Opening a supplier and seeing everything about them in one place.

"I'd like to open a supplier and see, clearly: this is what I bought, this is what I paid,
this is what I owe, and how long it's been. Also their email and CUIT, because today we look
them up in a notebook."
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from store import Store

from ..deps import get_store
from ..security import requires

router = APIRouter(prefix="/api/proveedores", tags=["proveedores"])


@router.get("")
def listing(store: Store = Depends(get_store), user: dict = Depends(requires("proveedores"))) -> dict:
    return {
        "proveedores": store.suppliers.positions(),
        "cumplimiento": store.suppliers.with_terms_compliance(),
    }


@router.get("/{slug}")
def detail(slug: str, store: Store = Depends(get_store), user: dict = Depends(requires("proveedores"))) -> dict:
    supplier = store.suppliers.by_slug(slug)
    if supplier is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"No existe el proveedor {slug}")

    supplier_id = supplier["id"]
    return {
        "proveedor": supplier,
        "posicion": store.suppliers.position(supplier_id),
        "alias": store.supplier_aliases.for_supplier(supplier_id),
        "facturas": store.invoices.listing(supplier_id=supplier_id),
        "pagos": store.payments.for_supplier(supplier_id),
        "ordenes": [o for o in store.orders.listing() if o["supplier_id"] == supplier_id],
        "mensajes": [m for m in store.messages.listing() if m["supplier_id"] == supplier_id],
    }
