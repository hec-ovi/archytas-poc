"""Who can enter, and what each one is allowed to see.

The client was explicit: Marcela handles purchases and suppliers, Julian handles sales and
the business numbers, and neither should see the other's side. The owner sees everything.
Roles are three, not a permission matrix, because three is what was asked for and a matrix
nobody maintains ends up granting everything.
"""

from __future__ import annotations

from typing import Any

from .base import Repository, decode_all

# what each role is allowed to open
ROLE_SECTIONS: dict[str, tuple[str, ...]] = {
    "duenio": ("tablero", "proveedores", "facturas", "ordenes", "calendario", "ventas", "productos", "revision", "mensajes", "configuracion"),
    "compras": ("proveedores", "facturas", "ordenes", "calendario", "revision", "mensajes"),
    "ventas": ("tablero", "ventas", "productos"),
}


class UserRepository(Repository):
    table = "app_user"

    def by_username(self, username: str) -> dict[str, Any] | None:
        return self.get_by("username", username)

    def save(self, values: dict[str, Any]) -> int:
        return self.upsert(values, ["username"])

    def listing(self) -> list[dict[str, Any]]:
        return decode_all(
            self.db.query("SELECT id, username, display_name, role, created_at FROM app_user ORDER BY username")
        )

    @staticmethod
    def sections_for(role: str) -> tuple[str, ...]:
        return ROLE_SECTIONS.get(role, ())


class SettingRepository(Repository):
    table = "setting"

    def get_value(self, key: str, default: Any = None) -> Any:
        row = self.db.one("SELECT value FROM setting WHERE key = ?", (key,))
        if row is None:
            return default
        from .database import loads
        decoded = loads(row["value"])
        return decoded.get("v", default) if isinstance(decoded, dict) and "v" in decoded else decoded

    def set_value(self, key: str, value: Any, user: str = "", label: str = "") -> None:
        from .database import dumps
        self.db.execute(
            """
            INSERT INTO setting (key, value, label, updated_by, updated_at)
            VALUES (?, ?, ?, ?, datetime('now'))
            ON CONFLICT (key) DO UPDATE SET
                value = excluded.value, updated_by = excluded.updated_by, updated_at = excluded.updated_at,
                label = CASE WHEN excluded.label <> '' THEN excluded.label ELSE setting.label END
            """,
            (key, dumps({"v": value}), label, user),
        )

    def all_settings(self) -> list[dict[str, Any]]:
        from .database import loads
        rows = self.db.query("SELECT key, value, label, updated_at, updated_by FROM setting ORDER BY key")
        for row in rows:
            decoded = loads(row["value"])
            row["value"] = decoded.get("v") if isinstance(decoded, dict) and "v" in decoded else decoded
        return rows
