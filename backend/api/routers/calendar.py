"""The calendar of due dates.

"We need a visual calendar where you can see at a glance when each invoice falls due, add a
new due date or move one that got rescheduled, and if two people are looking at it at the
same time, both see the change right away."

Moving a date keeps where it came from, and a date a person moved by hand is never
overwritten by the next sync.
"""

from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from store import Store

from ..deps import get_hub, get_store
from ..realtime import Hub
from ..security import requires

router = APIRouter(prefix="/api/calendario", tags=["calendario"])


class NewEvent(BaseModel):
    titulo: str = Field(min_length=1)
    fecha: str
    nota: str = ""
    factura_id: int | None = None
    proveedor_id: int | None = None
    monto_centavos: int | None = None


class MoveEvent(BaseModel):
    fecha: str


@router.get("")
def listing(desde: str | None = None, hasta: str | None = None,
            store: Store = Depends(get_store), user: dict = Depends(requires("calendario"))) -> dict:
    start = desde or (date.today() - timedelta(days=30)).isoformat()
    end = hasta or (date.today() + timedelta(days=90)).isoformat()
    return {"desde": start, "hasta": end, "eventos": store.calendar.between(start, end)}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create(body: NewEvent, store: Store = Depends(get_store), hub: Hub = Depends(get_hub),
                 user: dict = Depends(requires("calendario"))) -> dict:
    event_id = store.calendar.insert(
        {
            "title": body.titulo,
            "on_date": body.fecha,
            "kind": "recordatorio",
            "invoice_id": body.factura_id,
            "supplier_id": body.proveedor_id,
            "amount_cents": body.monto_centavos,
            "note": body.nota,
            "created_by": user["usuario"],
        }
    )
    event = store.calendar.get(event_id)
    await hub.broadcast("calendario-cambio", {"accion": "alta", "evento": event})
    return {"evento": event}


@router.patch("/{event_id}")
async def move(event_id: int, body: MoveEvent, store: Store = Depends(get_store), hub: Hub = Depends(get_hub),
               user: dict = Depends(requires("calendario"))) -> dict:
    event = store.calendar.move(event_id, body.fecha, user["usuario"])
    if event is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No existe ese vencimiento")
    await hub.broadcast("calendario-cambio", {"accion": "movido", "evento": event})
    return {"evento": event}


@router.delete("/{event_id}")
async def remove(event_id: int, store: Store = Depends(get_store), hub: Hub = Depends(get_hub),
                 user: dict = Depends(requires("calendario"))) -> dict:
    event = store.calendar.get(event_id)
    if event is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No existe ese vencimiento")
    if event.get("invoice_id"):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Ese vencimiento es de una factura: se saca borrando o anulando la factura, no del calendario",
        )
    store.calendar.delete(event_id)
    await hub.broadcast("calendario-cambio", {"accion": "baja", "evento": event})
    return {"ok": True}
