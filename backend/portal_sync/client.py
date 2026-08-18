"""Read access to the SIGProv portal.

Every dataset the portal exposes is a plain GET returning one JSON object with a single
list inside. This client returns those lists untouched: normalizing is someone else's job.
"""

from __future__ import annotations

import json
from typing import Any

from .errors import PortalBadResponse
from .session import PortalSession

# dataset name -> (path, key holding the list in the response)
DATASETS: dict[str, tuple[str, str]] = {
    "precios": ("/api/precios", "productos"),
    "facturas": ("/api/facturas", "facturas"),
    "ventas": ("/api/ventas", "ventas"),
    "categorias": ("/api/categorias", "categorias"),
    "ordenes_compra": ("/api/ordenes-compra", "ordenes"),
    "estado_cuenta": ("/api/estado-cuenta", "cuentas"),
    "comprobantes_pago": ("/api/comprobantes-pago", "pagos"),
    "catalogo": ("/api/catalogo", "items"),
    "mensajes": ("/api/mensajes", "mensajes"),
}


class PortalClient:
    """Fetches datasets. One method to get one dataset, one to get them all."""

    def __init__(self, session: PortalSession):
        self._session = session

    def dataset(self, name: str) -> list[dict[str, Any]]:
        if name not in DATASETS:
            raise KeyError(f"unknown dataset {name!r}; known: {sorted(DATASETS)}")
        path, list_key = DATASETS[name]
        payload = self._get_json(path)
        rows = payload.get(list_key)
        if not isinstance(rows, list):
            raise PortalBadResponse(f"{path} has no list under {list_key!r}")
        return rows

    def envelope(self, name: str) -> dict[str, Any]:
        """The whole response, for datasets that carry extra fields next to the list."""
        path, _ = DATASETS[name]
        return self._get_json(path)

    def all_datasets(self) -> dict[str, list[dict[str, Any]]]:
        return {name: self.dataset(name) for name in DATASETS}

    def price_history(self, product_id: str) -> list[dict[str, Any]]:
        """Every price this article has had, oldest first.

        The price list only shows today. This detail route is the only place the portal
        keeps history, and it is not linked from the menu.
        """
        payload = self._get_json(f"/api/precios/{product_id}")
        history = payload.get("historial")
        if not isinstance(history, list):
            raise PortalBadResponse(f"/api/precios/{product_id} has no historial list")
        return history

    def product_detail(self, product_id: str) -> dict[str, Any]:
        return self._get_json(f"/api/precios/{product_id}")

    def _get_json(self, path: str) -> dict[str, Any]:
        response = self._session.request("GET", path)
        if response.status_code != 200:
            raise PortalBadResponse(f"GET {path} returned {response.status_code}")
        try:
            payload = response.json()
        except json.JSONDecodeError as exc:
            raise PortalBadResponse(f"GET {path} is not JSON: {exc}") from exc
        if not isinstance(payload, dict):
            raise PortalBadResponse(f"GET {path} returned {type(payload).__name__}, expected object")
        return payload
