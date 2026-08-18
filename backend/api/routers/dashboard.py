"""The one screen that answers "how are we doing".

The client's complaint was not missing data, it was that nobody looks at it together. So
this returns the whole picture in one call: what we sold, what we owe, what is coming due,
and what the system refused to count, with the reason.
"""

from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends

from store import Store

from ..deps import get_store
from ..security import requires

router = APIRouter(prefix="/api/tablero", tags=["tablero"])


@router.get("")
def dashboard(store: Store = Depends(get_store), user: dict = Depends(requires("tablero"))) -> dict:
    today = date.today()
    horizon = (today + timedelta(days=30)).isoformat()

    health = store.sales.health()
    excluded = {k: v for k, v in health.items() if k != "valida"}

    return {
        "ventas_por_mes": store.sales.revenue_by_month(),
        "ventas_por_rubro": store.sales.revenue_by_category(),
        "productos_top": store.sales.top_products(8),
        "clientes_top": store.sales.top_customers(8),
        "salud_ventas": {
            "validas": health.get("valida", {"count": 0, "cents": 0}),
            "excluidas": excluded,
            "excluidas_total": sum(v["count"] for v in excluded.values()),
        },
        "estado_pagos": store.invoices.payment_summary(),
        "deuda_por_proveedor": store.suppliers.positions(),
        "gasto_por_rubro": store.categories.spend_by_category(),
        "vencen_pronto": store.invoices.due_between(today.isoformat(), horizon),
        "sin_recibo": store.invoices.without_receipt_due_before(horizon),
        "ordenes_olvidadas": store.orders.stale(int(store.settings.get_value("orden_vieja_dias", 30))),
        "pendientes_revision": store.reviews.pending_count(),
        "mensajes_abiertos": store.messages.open_count(),
        "productos_nuevos": store.products.new_since((today - timedelta(days=30)).isoformat()),
        "ultima_sincronizacion": store.runs.last_successful(),
    }
