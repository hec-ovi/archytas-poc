"""Who is asking, and whether they are allowed.

The client was explicit that a shared password is the problem, not the solution: Marcela
should not see the company's sales, Julian should not touch the supplier accounts. So a
session names one person, and every route states the section it belongs to. A role that
does not include that section gets a 403, whether or not it knows the URL.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, Request, status

from store import ROLE_SECTIONS, Store

COOKIE_NAME = "cordillera_sesion"
SESSION_DAYS = 7


class SessionSigner:
    """Signs and reads the session cookie."""

    def __init__(self, secret: str):
        self._secret = secret

    def issue(self, user: dict) -> str:
        payload = {
            "sub": user["username"],
            "rol": user["role"],
            "nombre": user["display_name"],
            "exp": datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS),
        }
        return jwt.encode(payload, self._secret, algorithm="HS256")

    def read(self, token: str) -> dict | None:
        try:
            return jwt.decode(token, self._secret, algorithms=["HS256"])
        except jwt.PyJWTError:
            return None


def current_user(request: Request) -> dict:
    """The person behind this request, or 401."""
    token = request.cookies.get(COOKIE_NAME)
    signer: SessionSigner = request.app.state.signer
    payload = signer.read(token) if token else None
    if payload is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sesion vencida o inexistente")
    return {
        "usuario": payload["sub"],
        "rol": payload["rol"],
        "nombre": payload["nombre"],
        "secciones": list(ROLE_SECTIONS.get(payload["rol"], ())),
    }


def requires(section: str):
    """Guard a router with the section it belongs to."""

    def guard(user: dict = Depends(current_user)) -> dict:
        if section not in user["secciones"]:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"Tu usuario no tiene acceso a {section}. Hablalo con el duenio.",
            )
        return user

    return guard
