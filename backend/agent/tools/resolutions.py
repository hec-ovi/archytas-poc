"""Closing what was waiting for a person.

Resolving a doubt about a supplier does two things at once: it closes the item, and it
teaches the catalog that spelling forever, so nobody is asked the same question twice. The
supplier has to exist: choosing one that is not in the catalog is refused, never created.
"""

from __future__ import annotations

from typing import Any

from ..errors import ToolError
from .base import Parameter, Tool


class ResolverRevision(Tool):
    name = "resolver_revision"
    section = "revision"
    needs_user = True
    parameters = (
        Parameter("pendiente_id", "integer", required=True),
        Parameter("proveedor_slug", "string"),
        Parameter("nota", "string"),
    )

    def run(self, pendiente_id: object = None, proveedor_slug: str = "", nota: str = "",
            usuario: str = "", **_: Any) -> dict[str, Any]:
        if not usuario:
            raise ToolError("No puedo resolver un pendiente sin saber quien lo pide")

        item = self._store.reviews.get(int(pendiente_id or 0))
        if item is None:
            raise ToolError(f"No existe el pendiente {pendiente_id}")
        if item["status"] != "pendiente":
            raise ToolError(f"El pendiente {item['id']} ya estaba {item['status']}")

        applied = self._apply(item, proveedor_slug)
        self._store.reviews.resolve(
            item["id"],
            {"proveedor_slug": proveedor_slug, "nota": nota, "aplicado": applied, "origen": "agente"},
            usuario,
        )
        return {
            "resuelto": item["id"],
            "aplicado": applied,
            "pendientes": self._store.reviews.pending_count(),
        }

    def _apply(self, item: dict[str, Any], slug: str) -> str:
        if not slug:
            return "queda cerrado con la nota, sin cambios automaticos"

        supplier = self._store.suppliers.by_slug(slug)
        if supplier is None:
            raise ToolError(f"No existe el proveedor {slug!r}. Solo se puede elegir uno del catalogo")
        if item["kind"] != "proveedor":
            return f"queda cerrado apuntando a {supplier['name']}"

        raw = item.get("raw", {})
        spelling = raw.get("proveedor") or raw.get("remitente") or ""
        if not spelling:
            return f"queda cerrado apuntando a {supplier['name']}, sin escritura que aprender"
        self._store.supplier_aliases.remember(supplier["id"], spelling, "persona", 1.0)
        return f"la escritura {spelling!r} queda asociada a {supplier['name']} para siempre"


class ResolverMensaje(Tool):
    name = "resolver_mensaje"
    section = "mensajes"
    needs_user = True
    parameters = (
        Parameter("mensaje_id", "integer", required=True),
        Parameter("nota", "string"),
    )

    def run(self, mensaje_id: object = None, nota: str = "", usuario: str = "", **_: Any) -> dict[str, Any]:
        if not usuario:
            raise ToolError("No puedo cerrar un mensaje sin saber quien lo pide")

        message = self._store.messages.get(int(mensaje_id or 0))
        if message is None:
            raise ToolError(f"No existe el mensaje {mensaje_id}")
        if message["resolved"]:
            return {"resuelto": message["id"], "nuevo": False, "abiertos": self._store.messages.open_count()}

        if nota:
            self._store.messages.update(
                message["id"], {"extra": {**message.get("extra", {}), "nota": nota, "origen": "agente"}}
            )
        self._store.messages.resolve(message["id"], usuario)
        return {"resuelto": message["id"], "nuevo": True, "abiertos": self._store.messages.open_count()}
