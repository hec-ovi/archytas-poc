"""The numbers the client tunes himself.

They live in the `setting` table so he can move a threshold from the screen without anyone
deploying, and they are read once per pass, so a change made at nine holds at ten.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from store import Store

from .dates import Clock


@dataclass(frozen=True)
class AlertSettings:
    """Everything a rule needs besides the database: the thresholds and today."""

    clock: Clock
    recibo_dias_antes: int = 5
    aviso_dias_antes: int = 7
    aviso_monto_minimo: int = 10_000_000
    orden_vieja_dias: int = 30
    aviso_maximo_por_regla: int = 5

    @classmethod
    def load(cls, store: Store, today: str | date | None = None) -> "AlertSettings":
        defaults = cls(clock=Clock(today))
        read = store.settings.get_value
        return cls(
            clock=defaults.clock,
            recibo_dias_antes=_whole(read("recibo_dias_antes"), defaults.recibo_dias_antes),
            aviso_dias_antes=_whole(read("aviso_dias_antes"), defaults.aviso_dias_antes),
            aviso_monto_minimo=_whole(read("aviso_monto_minimo"), defaults.aviso_monto_minimo),
            orden_vieja_dias=_whole(read("orden_vieja_dias"), defaults.orden_vieja_dias),
            aviso_maximo_por_regla=_whole(
                read("aviso_maximo_por_regla"), defaults.aviso_maximo_por_regla
            ),
        )

    @property
    def today(self) -> str:
        return self.clock.today


def _whole(value: Any, fallback: int) -> int:
    """A setting typed into a form arrives as text. A broken one falls back instead of failing."""
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return fallback
