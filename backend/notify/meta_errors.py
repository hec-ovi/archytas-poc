"""Meta's error codes turned into a reason a person can read.

Meta answers 4xx with a JSON `error` object carrying a numeric code. Only the codes this
box can actually hit are mapped; anything else is relayed with its code so the trail is
not lost.
"""

from __future__ import annotations

import httpx

REASONS: dict[int, str] = {
    131030: "el numero no esta en la lista de permitidos del numero de prueba de Meta",
    131047: "pasaron mas de 24 horas desde el ultimo mensaje del destinatario, hay que mandar una plantilla",
    131026: "el mensaje no se pudo entregar, el numero puede no tener WhatsApp o haber bloqueado a la empresa",
    190: "el token de acceso vencio o es invalido",
    132000: "la plantilla espera otra cantidad de parametros",
    132001: "no existe una plantilla con ese nombre e idioma",
}


class MetaError:
    """Reads Meta's error response and says, in plain Spanish, what went wrong."""

    def __init__(self, response: httpx.Response):
        self._status = response.status_code
        self._body = response.text
        try:
            self._error = response.json().get("error", {})
        except ValueError:
            self._error = {}

    @property
    def code(self) -> int | None:
        code = self._error.get("code")
        return code if isinstance(code, int) else None

    def reason(self) -> str:
        if not self._error:
            return f"WhatsApp respondio {self._status} sin un error legible: {self._body}"
        known = REASONS.get(self.code)
        if known:
            return f"{known} (codigo {self.code})"
        detail = self._error.get("error_data", {}).get("details") or self._error.get("message", "")
        return f"WhatsApp rechazo el envio (codigo {self.code}): {detail}"
