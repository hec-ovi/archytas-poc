"""Entering and leaving.

Three people, three roles, one password each. The shared login the client complained about
stays behind, in the portal, where it belongs to somebody else's system.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel

from store import Store, verify_password

from ..deps import get_settings, get_store
from ..security import COOKIE_NAME, SESSION_DAYS, SessionSigner, current_user

router = APIRouter(prefix="/api/auth", tags=["acceso"])


class Credentials(BaseModel):
    usuario: str
    clave: str


@router.post("/login")
def login(body: Credentials, response: Response, store: Store = Depends(get_store),
          settings=Depends(get_settings)) -> dict:
    user = store.users.by_username(body.usuario.strip().lower())
    if user is None or not verify_password(user.get("password_hash"), body.clave):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario o clave incorrectos")

    token = SessionSigner(settings.secret_key).issue(user)
    response.set_cookie(
        COOKIE_NAME, token, max_age=SESSION_DAYS * 86400,
        httponly=True, samesite="lax", path="/",
    )
    from store import ROLE_SECTIONS
    return {
        "usuario": user["username"],
        "nombre": user["display_name"],
        "rol": user["role"],
        "secciones": list(ROLE_SECTIONS.get(user["role"], ())),
    }


@router.post("/logout")
def logout(response: Response) -> dict:
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"ok": True}


@router.get("/me")
def me(user: dict = Depends(current_user)) -> dict:
    return user
