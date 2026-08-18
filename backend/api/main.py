"""The server.

Opens the database, wires the routes, and keeps one broadcast hub for the pages that are
open. A fresh database is created and seeded on start, so `docker compose up` on an empty
checkout gives a working system.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from store import Store

from .config import Settings
from .realtime import Hub
from .routers import analytics, auth, calendar, dashboard, documents, invoices, operations, suppliers, sync
from .security import SessionSigner


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings.from_env()
    app.state.settings = settings
    app.state.store = Store.open(str(settings.database_path))
    app.state.hub = Hub()
    app.state.signer = SessionSigner(settings.secret_key)
    yield
    app.state.store.close()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Cordillera",
        description="Sistema de gestion de Ferreteria Industrial Cordillera",
        version="1.0.0",
        lifespan=lifespan,
    )

    # the UI runs on its own port in development; in the container both are same origin
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    for module in (auth, dashboard, suppliers, invoices, calendar, operations, analytics, sync, documents):
        app.include_router(module.router)

    @app.get("/api/salud", tags=["salud"])
    def health() -> dict:
        store: Store = app.state.store
        return {
            "ok": True,
            "base": str(app.state.settings.database_path),
            "facturas": store.invoices.count(),
            "ventas": store.sales.count(),
            "paginas_abiertas": app.state.hub.connected,
        }

    @app.websocket("/ws")
    async def realtime(socket: WebSocket) -> None:
        """Open pages listen here. Nothing is read from them: it is a one-way channel."""
        hub: Hub = app.state.hub
        await hub.join(socket)
        try:
            while True:
                await socket.receive_text()
        except WebSocketDisconnect:
            await hub.leave(socket)
        except Exception:
            await hub.leave(socket)

    return app


app = create_app()
