"""Amounts, in whatever shape they arrive.

Argentina writes `$1.399.069,50`: dot for thousands, comma for decimals. Spreadsheets and
scanned invoices also produce `1399069.5`, `1,399,069.50` and bare numbers. Everything ends
as an integer number of cents, so no float ever touches a balance.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from .result import Normalized, resolved, unresolved

CLEAN = re.compile(r"[^\d,.\-]")
NEGATIVE_PARENS = re.compile(r"^\(.*\)$")


def parse_amount(raw: object) -> Normalized:
    """Turn anything money-shaped into cents (int). `"$223.376"` -> `22337600`."""
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return unresolved("", "empty amount")

    if isinstance(raw, (int, float, Decimal)) and not isinstance(raw, bool):
        return resolved(str(raw), _to_cents(Decimal(str(raw))), "numeric")

    text = str(raw).strip()
    negative = text.startswith("-") or bool(NEGATIVE_PARENS.match(text))
    digits = CLEAN.sub("", text).lstrip("-")
    if not digits or not any(ch.isdigit() for ch in digits):
        return unresolved(text, "no digits in amount")

    body, method = _separators(digits)
    try:
        amount = Decimal(body)
    except InvalidOperation:
        return unresolved(text, f"cannot read {digits!r} as a number")

    cents = _to_cents(-amount if negative else amount)
    return resolved(text, cents, method)


def format_amount(cents: int) -> str:
    """Cents back to what the client reads on screen: `22337600` -> `$223.376,00`."""
    sign = "-" if cents < 0 else ""
    whole, remainder = divmod(abs(cents), 100)
    grouped = f"{whole:,}".replace(",", ".")
    return f"{sign}${grouped},{remainder:02d}"


def _separators(digits: str) -> tuple[str, str]:
    """Decide which of `.` and `,` is the decimal mark, and drop the other."""
    last_dot, last_comma = digits.rfind("."), digits.rfind(",")

    if last_dot >= 0 and last_comma >= 0:
        # whichever comes last is the decimal mark
        if last_comma > last_dot:
            return digits.replace(".", "").replace(",", "."), "es-format"
        return digits.replace(",", ""), "en-format"

    if last_comma >= 0:
        tail = len(digits) - last_comma - 1
        if tail == 3 and digits.count(",") >= 1 and len(digits.replace(",", "")) > 3:
            return digits.replace(",", ""), "comma-thousands"
        return digits.replace(",", "."), "comma-decimal"

    if last_dot >= 0:
        tail = len(digits) - last_dot - 1
        # `223.376` is thousands here; `223.37` is decimals
        if tail == 3:
            return digits.replace(".", ""), "dot-thousands"
        return digits, "dot-decimal"

    return digits, "plain"


def _to_cents(amount: Decimal) -> int:
    return int((amount * 100).quantize(Decimal("1")))
