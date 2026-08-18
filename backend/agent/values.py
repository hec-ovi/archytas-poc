"""Turning what the model wrote into values the database accepts.

The model never parses a date and never converts an amount: it passes along what the person
said and these three functions hand it to `normalizer`, which is the only thing in the system
allowed to decide that `03/05/2026` is the third of May.

Anything that cannot be read comes back as a `ToolError` in Spanish, so the model can ask
again instead of writing a wrong number into the accounts.
"""

from __future__ import annotations

from datetime import date

from normalizer.dates import parse_date
from normalizer.money import format_amount

from .errors import ToolError


def as_cents(raw: object, field: str = "monto") -> int:
    """An amount in integer cents. Never a float, never a word."""
    if isinstance(raw, bool) or raw is None:
        raise ToolError(f"Falta {field} en centavos enteros")
    if isinstance(raw, int):
        return raw
    text = str(raw).strip().replace(" ", "")
    if text.lstrip("-").isdigit():
        return int(text)
    raise ToolError(
        f"No puedo leer {field} de {raw!r}. Tiene que venir en centavos enteros, sin puntos ni palabras: "
        f"doscientos mil pesos son 20000000"
    )


def as_date(raw: object, field: str = "fecha") -> str:
    """A date in ISO, read by the normalizer in whatever shape it arrived."""
    result = parse_date(raw)
    if not result.resolved:
        raise ToolError(f"No puedo leer {field} de {raw!r}: {result.reason or 'no parece una fecha'}")
    return str(result.value)


def as_money(cents: object) -> str:
    """Cents as the client reads them on screen."""
    if cents is None:
        return ""
    return format_amount(int(cents))


def today() -> str:
    return date.today().isoformat()
