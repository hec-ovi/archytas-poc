"""Refreshing from the portal.

The client asked to be able to change how often this runs without calling anyone, so the
interval is a setting, not a constant. He can also press the button whenever he wants: the
portal updates twice a day, and waiting for a schedule when you already know something
changed is exactly the friction he complained about.
"""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends

from ingest import IngestRunner
from store import Store

from ..deps import get_hub, get_settings, get_store, open_portal
from ..realtime import Hub
from ..security import current_user, requires

router = APIRouter(prefix="/api/sync", tags=["sincronizacion"])


@router.get("/estado")
def status(store: Store = Depends(get_store), user: dict = Depends(current_user)) -> dict:
    return {
        "ultima_ok": store.runs.last_successful(),
        "pasadas": store.runs.latest(10),
        "cada_horas": store.settings.get_value("sync_horas", 12),
    }


@router.post("")
async def run_now(background: BackgroundTasks, con_historial: bool = False,
                  store: Store = Depends(get_store), settings=Depends(get_settings),
                  hub: Hub = Depends(get_hub), user: dict = Depends(requires("configuracion"))) -> dict:
    """Kick off a pass and answer immediately: a full pass takes longer than a page will wait."""
    background.add_task(_pass, store, settings, hub, con_historial, user["usuario"])
    return {"lanzada": True, "con_historial": con_historial}


async def _pass(store: Store, settings, hub: Hub, with_history: bool, username: str) -> None:
    session, client = open_portal(settings)
    try:
        report = IngestRunner(store, client).run(trigger=f"manual:{username}", with_price_history=with_history)
    finally:
        session.close()
    await hub.broadcast("sincronizacion-lista", report.as_dict())
