"""The two lists of things waiting for a person: what the system refused to guess, and the inbox."""

from __future__ import annotations

from typing import Any

from .base import Parameter, Tool


class ConsultarRevision(Tool):
    name = "consultar_revision"
    parameters = (Parameter("tipo", "string"),)

    def run(self, tipo: str = "", **_: Any) -> dict[str, Any]:
        items = [
            {
                "id": row["id"],
                "tipo": row["kind"],
                "titulo": row["title"],
                "detalle": row["detail"],
                "candidatos": row["candidates"],
                "creado": row["created_at"],
            }
            for row in self._store.reviews.pending(tipo or None)
        ]
        return {"pendientes": items, "cantidad": len(items), "resumen": self._store.reviews.summary()}


class ConsultarMensajes(Tool):
    name = "consultar_mensajes"
    parameters = (Parameter("solo_abiertos", "boolean"),)

    def run(self, solo_abiertos: object = True, **_: Any) -> dict[str, Any]:
        only_open = bool(solo_abiertos) if solo_abiertos is not None else True
        messages = [
            {
                "id": row["id"],
                "fecha": row["received_on"],
                "de": row["sender"],
                "proveedor": row.get("supplier_name"),
                "asunto": row["subject"],
                "texto": row["body"],
                "tipo": row["kind"],
                "factura": row.get("invoice_number"),
                "resuelto": bool(row["resolved"]),
            }
            for row in self._store.messages.listing(only_open=only_open)
        ]
        return {"mensajes": messages, "abiertos": self._store.messages.open_count()}
