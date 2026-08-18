"""Reading one raw value as one invoice field.

The same six fields arrive as a piece of a text line, as a spreadsheet cell, or as an OCR
guess. This is the single place that turns any of those into a canonical value, leaning on
the normalizer for dates and amounts, and it always explains itself in Spanish.
"""

from __future__ import annotations

import re

from normalizer.dates import parse_date
from normalizer.money import parse_amount
from normalizer.result import Normalized, resolved, unresolved

from .cuit import CuitReader
from .vocabulary import FIELD_LABELS

# "F-8411", "REC-1650", "0001-00012345", "A 1234"
NUMBER_SHAPE = re.compile(r"^[A-Za-z]{0,6}[ ./-]?\d{2,}(?:[-/]\d{1,8})?$")

# a supplier name written on the same line as its CUIT
TRAILING_CUIT = re.compile(r"\s*[-,]?\s*(?:cuit|cuil)\b.*$", re.IGNORECASE)


class ValueReader:
    """One raw value in, a `Normalized` out. Never raises, never guesses."""

    def __init__(self) -> None:
        self._cuit = CuitReader()

    def read(self, field: str, raw: object) -> Normalized:
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            return unresolved("", f"no hay {FIELD_LABELS[field]}")

        readers = {
            "fecha": self._date,
            "vencimiento": self._date,
            "total": self._amount,
            "numero": self._number,
            "proveedor": self._name,
            "cuit": self._cuit.of_value,
        }
        return readers[field](raw)

    def _date(self, raw: object) -> Normalized:
        reading = parse_date(raw)
        if reading.value is None:
            return unresolved(str(raw), f"'{_short(raw)}' no tiene forma de fecha")
        return reading

    def _amount(self, raw: object) -> Normalized:
        reading = parse_amount(raw)
        if reading.value is None:
            return unresolved(str(raw), f"'{_short(raw)}' no tiene forma de importe")
        return reading

    @staticmethod
    def _number(raw: object) -> Normalized:
        text = str(raw).strip()
        if not NUMBER_SHAPE.match(text):
            return unresolved(text, f"'{_short(text)}' no tiene forma de numero de comprobante")
        return resolved(text, text.upper(), "etiqueta")

    @staticmethod
    def _name(raw: object) -> Normalized:
        text = TRAILING_CUIT.sub("", str(raw).strip()).strip(" ,;-")
        if len(text) < 3 or not any(char.isalpha() for char in text):
            return unresolved(str(raw), f"'{_short(raw)}' no parece un nombre de proveedor")
        # the identity behind the name is the normalizer's catalog job, not this box's
        return resolved(str(raw), text, "etiqueta")


def ambiguity(field: str, readings: list[tuple]) -> str | None:
    """The message for several readings that disagree, or `None` when they all agree.

    Shared by the two ways a field is found (a label in text, a label cell in a sheet):
    finding two answers is never resolved by taking the first one.
    """
    if len({reading.value for *_, reading in readings}) <= 1:
        return None
    shown = ", ".join(sorted(f"'{raw}'" for _, raw, _ in readings))
    return f"hay mas de un valor posible para {FIELD_LABELS[field]}: {shown}"


def _short(raw: object) -> str:
    text = " ".join(str(raw).split())
    return text if len(text) <= 40 else text[:37] + "..."
