"""What a fresh database needs before anyone can use it.

The three people the client named, and the settings he asked to be able to change himself
without calling anyone: how often the system refreshes, how many days ahead it warns, and
from what amount something is worth interrupting him for.
"""

from __future__ import annotations

from typing import Any

from .accounts import SettingRepository, UserRepository
from .database import Database
from .passwords import hash_password

DEFAULT_USERS = [
    ("marcela", "Marcela", "compras"),
    ("julian", "Julian", "ventas"),
    ("duenio", "Duenio", "duenio"),
]

DEFAULT_SETTINGS: list[tuple[str, Any, str]] = [
    ("sync_horas", 12, "Cada cuantas horas se actualiza desde el portal"),
    ("aviso_dias_antes", 7, "Cuantos dias antes del vencimiento avisar"),
    ("aviso_monto_minimo", 10000000, "Monto en centavos a partir del cual avisar"),
    ("orden_vieja_dias", 30, "A los cuantos dias una orden sin recibir se considera olvidada"),
    ("recibo_dias_antes", 5, "Cuantos dias antes del vencimiento reclamar el recibo faltante"),
    ("aviso_maximo_por_regla", 5, "Cuantos avisos sueltos manda una regla antes de mandar un resumen"),
]


def bootstrap(db: Database, default_password: str = "cordillera2026") -> dict[str, Any]:
    """Create the schema if missing, then the people and settings if missing. Safe to rerun."""
    db.create_schema()

    users = UserRepository(db)
    created = []
    for username, display_name, role in DEFAULT_USERS:
        if users.by_username(username) is None:
            users.save(
                {
                    "username": username,
                    "display_name": display_name,
                    "password_hash": hash_password(default_password),
                    "role": role,
                }
            )
            created.append(username)

    settings = SettingRepository(db)
    for key, value, label in DEFAULT_SETTINGS:
        if settings.get_value(key) is None:
            settings.set_value(key, value, user="sistema", label=label)

    return {"usuarios_creados": created, "usuarios": [u["username"] for u in users.listing()]}
