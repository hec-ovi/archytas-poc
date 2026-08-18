"""Purchase orders, the inbox, the review queue and the settings.

Four small surfaces that share a shape: a list, and one action that closes something. They
live together because splitting them into four files would be four files of thirty lines.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from store import Store

from ..deps import get_hub, get_store
from ..realtime import Hub
from ..security import current_user, requires

router = APIRouter(prefix="/api", tags=["operacion"])


class Resolution(BaseModel):
    decision: dict = {}


class SettingValue(BaseModel):
    valor: object


@router.get("/ordenes")
def orders(store: Store = Depends(get_store), user: dict = Depends(requires("ordenes"))) -> dict:
    stale_days = int(store.settings.get_value("orden_vieja_dias", 30))
    return {
        "ordenes": store.orders.listing(),
        "olvidadas": store.orders.stale(stale_days),
        "por_estado": store.orders.by_state(),
        "dias_para_olvidada": stale_days,
    }


@router.get("/mensajes")
def messages(abiertos: bool = False, store: Store = Depends(get_store),
             user: dict = Depends(requires("mensajes"))) -> dict:
    return {
        "mensajes": store.messages.listing(only_open=abiertos),
        "por_tipo": store.messages.by_kind(),
        "abiertos": store.messages.open_count(),
    }


@router.post("/mensajes/{message_id}/resolver")
def resolve_message(message_id: int, store: Store = Depends(get_store),
                    user: dict = Depends(requires("mensajes"))) -> dict:
    if store.messages.get(message_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No existe ese mensaje")
    store.messages.resolve(message_id, user["usuario"])
    return {"mensaje": store.messages.get(message_id), "abiertos": store.messages.open_count()}


@router.get("/revision")
def review_queue(tipo: str | None = None, store: Store = Depends(get_store),
                 user: dict = Depends(requires("revision"))) -> dict:
    return {"pendientes": store.reviews.pending(tipo), "resumen": store.reviews.summary()}


@router.post("/revision/{item_id}/resolver")
async def resolve_review(item_id: int, body: Resolution, store: Store = Depends(get_store),
                         hub: Hub = Depends(get_hub), user: dict = Depends(requires("revision"))) -> dict:
    item = store.reviews.get(item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No existe ese pendiente")

    applied = _apply_review(store, item, body.decision, user["usuario"])
    store.reviews.resolve(item_id, {**body.decision, "aplicado": applied}, user["usuario"])
    await hub.broadcast("revision-cambio", {"id": item_id, "pendientes": store.reviews.pending_count()})
    return {"aplicado": applied, "pendientes": store.reviews.pending_count()}


@router.post("/revision/{item_id}/descartar")
async def dismiss_review(item_id: int, store: Store = Depends(get_store), hub: Hub = Depends(get_hub),
                         user: dict = Depends(requires("revision"))) -> dict:
    if store.reviews.get(item_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No existe ese pendiente")
    store.reviews.dismiss(item_id, user["usuario"])
    await hub.broadcast("revision-cambio", {"id": item_id, "pendientes": store.reviews.pending_count()})
    return {"pendientes": store.reviews.pending_count()}


@router.get("/configuracion")
def settings_listing(store: Store = Depends(get_store), user: dict = Depends(requires("configuracion"))) -> dict:
    return {"configuracion": store.settings.all_settings()}


@router.put("/configuracion/{key}")
def set_setting(key: str, body: SettingValue, store: Store = Depends(get_store),
                user: dict = Depends(requires("configuracion"))) -> dict:
    if store.settings.get_value(key) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"No existe el parametro {key}")
    store.settings.set_value(key, body.valor, user=user["usuario"])
    return {"configuracion": store.settings.all_settings()}


@router.get("/alertas")
def alerts(store: Store = Depends(get_store), user: dict = Depends(current_user)) -> dict:
    return {
        "recientes": store.alerts.recent(30),
        "sin_ver": store.alerts.unacknowledged(),
        "entregas_fallidas": store.deliveries.failed(),
    }


@router.post("/alertas/revisar")
async def check_now(request: Request, store: Store = Depends(get_store), hub: Hub = Depends(get_hub),
                    user: dict = Depends(requires("configuracion"))) -> dict:
    """The "check now" button: run the rules against the current state and deliver what is new."""
    report = request.app.state.alerts.run()
    await hub.broadcast("avisos-revisados", report.as_dict())
    return {"resumen": report.as_dict(), "recientes": store.alerts.recent(20)}


@router.post("/alertas/{event_id}/visto")
def acknowledge(event_id: int, store: Store = Depends(get_store), user: dict = Depends(current_user)) -> dict:
    store.alerts.acknowledge(event_id)
    return {"sin_ver": store.alerts.unacknowledged()}


def _apply_review(store: Store, item: dict, decision: dict, username: str) -> str:
    """Turn a person's answer into the change it implies, and remember it for next time."""
    kind = item["kind"]

    if kind == "proveedor" and decision.get("proveedor_slug"):
        supplier = store.suppliers.by_slug(decision["proveedor_slug"])
        if supplier is None:
            return "el proveedor elegido no existe"
        spelling = item.get("raw", {}).get("proveedor") or item.get("raw", {}).get("remitente", "")
        store.supplier_aliases.remember(supplier["id"], spelling, "persona", 1.0)
        return f"la escritura {spelling!r} queda asociada a {supplier['name']} para siempre"

    if kind == "rubro" and decision.get("rubro_slug"):
        category = store.categories.get_by("slug", decision["rubro_slug"])
        if category is None:
            return "el rubro elegido no existe"
        spelling = item.get("raw", {}).get("categoria", "")
        store.category_aliases.remember(category["id"], spelling, "persona", 1.0)
        code = item.get("raw", {}).get("id")
        product = store.products.by_external(code) if code else None
        if product:
            store.products.update(product["id"], {"category_id": category["id"]})
        return f"la escritura {spelling!r} queda como {category['name']}"

    code = item["dedupe_key"].split(":", 1)[1]

    if kind == "venta-duplicada" and decision.get("codigo_valido"):
        keep = decision.get("row_hash")
        for sale in store.sales.by_code(code):
            store.sales.flag(
                sale["id"],
                "valida" if sale["row_hash"] == keep else "duplicada",
                f"decidido por {username}",
            )
        return "la venta elegida vuelve a sumar y las otras quedan marcadas como duplicadas"

    if kind == "venta-rota" and decision.get("valor_elegido") is not None:
        # the system worked the correction out but refused to apply it on its own. Which
        # column it belongs in travels with the candidate, so the caller only sends the value.
        corrected = int(decision["valor_elegido"])
        candidate = next((c for c in item.get("candidates", []) if c.get("valor") == corrected), {})
        column = candidate.get("campo", "total_cents")
        for sale in store.sales.by_code(code):
            values = {column: corrected}
            if column == "quantity" and sale.get("unit_cents"):
                values["total_cents"] = corrected * sale["unit_cents"]
            store.sales.update(sale["id"], values)
            store.sales.flag(sale["id"], "valida", f"corregido a mano por {username}")
        nombre = "la cantidad" if column == "quantity" else "el total"
        return f"la venta {code} vuelve a sumar con {nombre} corregido"

    return "sin cambios automaticos: queda registrado quien lo reviso"
