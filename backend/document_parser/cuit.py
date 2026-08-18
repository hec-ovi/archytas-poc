"""CUITs, and whose they are.

An invoice usually carries two: the supplier's and ours. Taking the wrong one is worse than
taking none, so a CUIT is only accepted as the supplier's when the surrounding lines say so.

The check digit is verified but never used to reject: a CUIT that does not close is still
reported, with low confidence, because that is exactly the shape of an OCR digit error.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from normalizer.result import Normalized, resolved, unresolved
from normalizer.text import fold

from .vocabulary import CLIENT_MARKERS, SUPPLIER_MARKERS

CUIT_PATTERN = re.compile(r"\b(\d{2})[-. ]?(\d{8})[-. ]?(\d)\b")
CHECK_WEIGHTS = (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)

OWNER_SUPPLIER = "proveedor"
OWNER_CLIENT = "cliente"
OWNER_UNKNOWN = "sin dueno"


@dataclass(frozen=True)
class Cuit:
    """One CUIT found in a document, formatted, with whose it looks to be."""

    value: str
    owner: str
    line: int
    check_ok: bool


class CuitReader:
    """Finds CUITs in text and decides which one belongs to the supplier."""

    def read(self, text: str) -> list[Cuit]:
        """Every CUIT in the text, in order, each tagged with the owner of its line."""
        found: list[Cuit] = []
        owner = OWNER_UNKNOWN
        for number, line in enumerate(text.splitlines(), start=1):
            owner = self._owner_of(line, owner)
            for match in CUIT_PATTERN.finditer(line):
                value = f"{match[1]}-{match[2]}-{match[3]}"
                found.append(Cuit(value, owner, number, self.check_digit_ok(value)))
        return found

    def supplier(self, text: str) -> Normalized:
        """The supplier's CUIT, or an unresolved value saying why there is none."""
        found = self.read(text)
        if not found:
            return unresolved("", "el documento no trae ningun CUIT")

        mine = [item for item in found if item.owner == OWNER_SUPPLIER]
        if not mine:
            owners = ", ".join(sorted({item.owner for item in found}))
            return unresolved(found[0].value, f"los CUIT del documento son del {owners}")

        values = {item.value for item in mine}
        if len(values) > 1:
            listed = ", ".join(sorted(values))
            return unresolved(listed, f"hay mas de un CUIT del proveedor: {listed}")

        return self.of_value(mine[0].value)

    def of_value(self, raw: object) -> Normalized:
        """Read a value that should already be a CUIT, like a spreadsheet cell."""
        text = str(raw or "").strip()
        match = CUIT_PATTERN.search(text)
        if not match:
            return unresolved(text, "no tiene forma de CUIT (NN-NNNNNNNN-N)")
        value = f"{match[1]}-{match[2]}-{match[3]}"
        if not self.check_digit_ok(value):
            return Normalized(
                raw=text, value=value, confidence=0.75, method="cuit",
                reason="el digito verificador no cierra, confirmar el numero",
            )
        return resolved(text, value, "cuit")

    @staticmethod
    def check_digit_ok(value: str) -> bool:
        digits = [int(char) for char in value if char.isdigit()]
        if len(digits) != 11:
            return False
        total = sum(weight * digit for weight, digit in zip(CHECK_WEIGHTS, digits))
        remainder = 11 - (total % 11)
        expected = 0 if remainder == 11 else (9 if remainder == 10 else remainder)
        return expected == digits[-1]

    @staticmethod
    def _owner_of(line: str, current: str) -> str:
        """A line that names the supplier or the client sets the owner for what follows."""
        folded = fold(line)
        positions = [(folded.find(marker), OWNER_SUPPLIER) for marker in SUPPLIER_MARKERS]
        positions += [(folded.find(marker), OWNER_CLIENT) for marker in CLIENT_MARKERS]
        hits = [(at, owner) for at, owner in positions if at >= 0]
        return min(hits)[1] if hits else current
