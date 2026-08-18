"""Invoice fields out of free text.

Works on whatever the PDF gave: a text layer or an OCR pass. Every field is looked up by
its label at the start of a line, tier by tier. Two different values under the same tier is
not a coin flip: the field comes back unreadable, naming both.
"""

from __future__ import annotations

import re

from .cuit import CuitReader
from .result import (
    INVOICE_FIELDS,
    KIND_INVOICE,
    KIND_RECEIPT,
    KIND_UNKNOWN,
    ExtractedField,
    Record,
    Unreadable,
)
from .values import ValueReader
from .vocabulary import FIELD_LABELS, TEXT_LABELS, TIER_WEIGHTS

MIN_READABLE_CHARS = 20


def _patterns(keyword: str) -> tuple[re.Pattern[str], ...]:
    """A label at the start of a line: with a colon (and filler words), or bare."""
    word = re.escape(keyword)
    return (
        re.compile(rf"^\s*{word}(?!\w)[^:\n]{{0,30}}:\s*(?P<value>\S.*?)\s*$", re.IGNORECASE),
        re.compile(rf"^\s*{word}(?!\w)\.?\s+(?P<value>\S.*?)\s*$", re.IGNORECASE),
    )


LABEL_PATTERNS = {
    field: tuple(tuple(_patterns(word) for word in tier) for tier in tiers)
    for field, tiers in TEXT_LABELS.items()
}


class FieldExtractor:
    """Text in, one `Record` out. `weight` discounts everything, for OCR text."""

    def __init__(self, weight: float = 1.0) -> None:
        self._weight = weight
        self._values = ValueReader()
        self._cuit = CuitReader()

    def classify(self, text: str) -> str:
        """What the document says it is, by the first line that names itself."""
        for line in text.splitlines():
            folded = line.strip().lower()
            if "recibo" in folded:
                return KIND_RECEIPT
            if "factura" in folded:
                return KIND_INVOICE
        return KIND_UNKNOWN

    def extract(self, text: str, origin: str) -> Record:
        """`origin` says where the text came from, and ends up on every field."""
        if len(text.strip()) < MIN_READABLE_CHARS:
            return Record(
                fields={},
                unreadable=tuple(
                    Unreadable(name, "el documento no dejo texto legible") for name in INVOICE_FIELDS
                ),
            )

        lines = text.splitlines()
        fields: dict[str, ExtractedField] = {}
        unreadable: list[Unreadable] = []
        for name in INVOICE_FIELDS:
            found = self._cuit_field(text, origin) if name == "cuit" else self._field(name, lines, origin)
            if isinstance(found, ExtractedField):
                fields[name] = found
            else:
                unreadable.append(found)
        return Record(fields=fields, unreadable=tuple(unreadable))

    def _field(self, name: str, lines: list[str], origin: str) -> ExtractedField | Unreadable:
        rejected: list[str] = []
        for tier, tier_patterns in enumerate(LABEL_PATTERNS[name]):
            hits = self._hits(tier_patterns, lines)
            readings = []
            for line_number, raw in hits:
                reading = self._values.read(name, raw)
                if reading.value is None:
                    rejected.append(reading.reason)
                else:
                    readings.append((line_number, raw, reading))

            if not readings:
                continue
            if len({reading.value for _, _, reading in readings}) > 1:
                shown = ", ".join(sorted(f"'{raw}'" for _, raw, _ in readings))
                return Unreadable(name, f"hay mas de un valor posible para {FIELD_LABELS[name]}: {shown}")

            line_number, raw, reading = readings[0]
            return ExtractedField(
                name=name,
                value=reading.value,
                raw=raw,
                confidence=reading.confidence * TIER_WEIGHTS[tier] * self._weight,
                source=f"{origin}, linea {line_number}",
                method=reading.method,
                reason=reading.reason,
            )

        if rejected:
            return Unreadable(name, rejected[0])
        return Unreadable(name, f"no aparece {FIELD_LABELS[name]} en el documento")

    def _cuit_field(self, text: str, origin: str) -> ExtractedField | Unreadable:
        reading = self._cuit.supplier(text)
        if reading.value is None:
            return Unreadable("cuit", reading.reason)
        return ExtractedField(
            name="cuit",
            value=reading.value,
            raw=reading.raw,
            confidence=reading.confidence * self._weight,
            source=origin,
            method=reading.method,
            reason=reading.reason,
        )

    @staticmethod
    def _hits(tier, lines: list[str]) -> list[tuple[int, str]]:
        """Every line that carries one of this tier's labels, at most one hit per line."""
        found: list[tuple[int, str]] = []
        for number, line in enumerate(lines, start=1):
            matches = (pattern.match(line) for patterns in tier for pattern in patterns)
            match = next(filter(None, matches), None)
            if match:
                found.append((number, match.group("value")))
        return found
