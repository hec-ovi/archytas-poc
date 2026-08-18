"""Sales and products: the numbers Julian looks at.

Everything here reads from `sale_valid`, which is the sales that can be trusted. The rows
that were left out are returned alongside, with their reason, so a total is never quietly
smaller than reality without saying why.
"""

from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status

from store import Store

from ..deps import get_store
from ..security import requires

router = APIRouter(prefix="/api", tags=["ventas y productos"])


@router.get("/ventas")
def sales(store: Store = Depends(get_store), user: dict = Depends(requires("ventas"))) -> dict:
    return {
        "por_mes": store.sales.revenue_by_month(),
        "por_rubro": store.sales.revenue_by_category(),
        "productos_top": store.sales.top_products(15),
        "clientes_top": store.sales.top_customers(15),
        "salud": store.sales.health(),
        "excluidas": store.sales.excluded(),
    }


@router.get("/productos")
def products(store: Store = Depends(get_store), user: dict = Depends(requires("productos"))) -> dict:
    return {
        "productos": store.products.listing(),
        "sin_rubro": store.products.without_category(),
        "stock": store.products.stock_snapshot(),
        "nuevos": store.products.new_since((date.today() - timedelta(days=30)).isoformat()),
        "precio_promedio_por_mes": store.prices.average_by_month(),
    }


@router.get("/productos/{product_id}/precios")
def price_history(product_id: int, store: Store = Depends(get_store),
                  user: dict = Depends(requires("productos"))) -> dict:
    product = store.products.get(product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No existe ese producto")
    return {"producto": product, "historial": store.prices.for_product(product_id)}
