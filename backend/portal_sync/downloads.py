"""File downloads from the portal.

Downloads take two steps: ask for a token, then follow the signed URL it hands back.
The signed URL carries its own timestamp and expires, so it is fetched right away and
never stored.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .errors import DownloadExpired, PortalBadResponse
from .session import PortalSession

TOKEN_PATH = "/api/token"

# The portal accepts exactly these eight kinds, each with its own idea of what an id is.
# Anything else comes back as "pedido invalido".
KINDS: dict[str, str] = {
    "precios": "el `archivoId` de /api/precios, hoy `lista-precios-actual`",
    "historial": "id de producto, `p1`",
    "factura": "id de factura, `f89`",
    "ventas": "el `archivoId` de /api/ventas, hoy `ventas-historico`",
    "categoria": "slug de rubro, `ferreteria-gral`",
    "cuenta": "slug de proveedor, `aceros-belgrano-sa`",
    "recibos": "el texto `listado`",
    "recibo": "id de pago, `pago-f7-1`",
}

# A signed link lives 45 seconds. It is minted right before the download and never stored.
TOKEN_TTL_SECONDS = 45


@dataclass(frozen=True)
class DownloadedFile:
    """Bytes as the portal served them, plus what the portal called the file."""

    filename: str
    content_type: str
    content: bytes

    @property
    def size(self) -> int:
        return len(self.content)


class PortalDownloader:
    """Turns a (kind, id) pair into the file behind it."""

    def __init__(self, session: PortalSession):
        self._session = session

    def signed_url(self, kind: str, item_id: str) -> str:
        if kind not in KINDS:
            raise PortalBadResponse(f"unknown download kind {kind!r}; known: {sorted(KINDS)}")
        response = self._session.request("POST", TOKEN_PATH, json={"kind": kind, "id": item_id})
        if response.status_code != 200:
            raise PortalBadResponse(f"token for {kind}:{item_id} returned {response.status_code}")
        payload = response.json()
        url = payload.get("url")
        if not url:
            raise PortalBadResponse(f"token for {kind}:{item_id} refused: {payload}")
        return url

    def fetch(self, kind: str, item_id: str) -> DownloadedFile:
        url = self.signed_url(kind, item_id)
        response = self._session.request("GET", url)
        if response.status_code in (403, 410):
            raise DownloadExpired(f"signed link for {kind}:{item_id} was refused")
        if response.status_code != 200:
            raise PortalBadResponse(f"download {kind}:{item_id} returned {response.status_code}")
        return DownloadedFile(
            filename=_filename_from(response.headers, fallback=f"{kind}-{item_id}"),
            content_type=response.headers.get("content-type", "application/octet-stream"),
            content=response.content,
        )


def _filename_from(headers, fallback: str) -> str:
    disposition = headers.get("content-disposition", "")
    match = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)"?', disposition)
    return match.group(1) if match else fallback
