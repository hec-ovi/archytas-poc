"""Dates, in whatever shape they arrive.

The portal serves ISO dates, but invoices and spreadsheets carry whatever the person typing
felt like. Argentina writes day first, so `03/05/2026` is 3 May, and that is the tie-break
used whenever both readings are possible.
"""

from __future__ import annotations

import re
from datetime import date, datetime

from .result import Normalized, resolved, unresolved

SPANISH_MONTHS = {
    "ene": 1, "enero": 1, "feb": 2, "febrero": 2, "mar": 3, "marzo": 3,
    "abr": 4, "abril": 4, "may": 5, "mayo": 5, "jun": 6, "junio": 6,
    "jul": 7, "julio": 7, "ago": 8, "agosto": 8, "sep": 9, "sept": 9, "septiembre": 9,
    "oct": 10, "octubre": 10, "nov": 11, "noviembre": 11, "dic": 12, "diciembre": 12,
}

ISO = re.compile(r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})$")
DMY = re.compile(r"^(\d{1,2})[-/.](\d{1,2})[-/.](\d{2,4})$")
TEXTUAL = re.compile(r"^(\d{1,2})\s*(?:de\s+)?[-/ ]?([a-zA-Z]+)\.?\s*(?:de\s+)?[-/ ]?(\d{2,4})$")
COMPACT = re.compile(r"^(\d{4})(\d{2})(\d{2})$")

# Excel serial dates: days since 1899-12-30 under the 1900 system
EXCEL_EPOCH = date(1899, 12, 30)
EXCEL_MIN, EXCEL_MAX = 20000, 60000  # roughly 1954 to 2064


def parse_date(raw: object) -> Normalized:
    """Turn anything date-shaped into an ISO `YYYY-MM-DD` string."""
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return unresolved("", "empty date")

    if isinstance(raw, datetime):
        return resolved(raw.isoformat(), raw.date().isoformat(), "datetime")
    if isinstance(raw, date):
        return resolved(raw.isoformat(), raw.isoformat(), "date")
    if isinstance(raw, (int, float)) and EXCEL_MIN <= raw <= EXCEL_MAX:
        value = EXCEL_EPOCH.toordinal() + int(raw)
        return resolved(str(raw), date.fromordinal(value).isoformat(), "excel-serial", 0.95)

    text = str(raw).strip()
    for parser in (_iso, _compact, _textual, _day_first):
        result = parser(text)
        if result is not None:
            return result
    return unresolved(text, "no known date format matched")


def _build(year: int, month: int, day: int, raw: str, method: str, confidence: float = 1.0) -> Normalized | None:
    if year < 100:
        year += 2000 if year < 70 else 1900
    try:
        return resolved(raw, date(year, month, day).isoformat(), method, confidence)
    except ValueError:
        return None


def _iso(text: str) -> Normalized | None:
    match = ISO.match(text)
    return _build(int(match[1]), int(match[2]), int(match[3]), text, "iso") if match else None


def _compact(text: str) -> Normalized | None:
    match = COMPACT.match(text)
    return _build(int(match[1]), int(match[2]), int(match[3]), text, "compact") if match else None


def _textual(text: str) -> Normalized | None:
    match = TEXTUAL.match(text)
    if not match:
        return None
    month = SPANISH_MONTHS.get(match[2].lower().strip("."))
    if month is None:
        return None
    return _build(int(match[3]), month, int(match[1]), text, "textual")


def _day_first(text: str) -> Normalized | None:
    """`03/05/2026` is 3 May here. When the first number cannot be a day, read it as US order."""
    match = DMY.match(text)
    if not match:
        return None
    first, second, year = int(match[1]), int(match[2]), int(match[3])

    if first > 12 and second <= 12:
        return _build(year, second, first, text, "day-first")
    if second > 12 and first <= 12:
        return _build(year, first, second, text, "month-first", 0.95)
    # both readings are valid: take the local convention, but flag it as a judgement call
    ambiguous = first != second and first <= 12 and second <= 12
    return _build(year, second, first, text, "day-first", 0.93 if ambiguous else 1.0)
