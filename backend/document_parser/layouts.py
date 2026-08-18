"""The two shapes a spreadsheet arrives in.

Either every row is a document (a table of invoices, of receipts, of movements), or the
whole sheet is one document written as label and value pairs. Both are read here; deciding
which one applies is the reader's job.
"""

from __future__ import annotations

from openpyxl.utils import get_column_letter

from .headers import TOKEN, ColumnMap, HeaderMatcher
from .result import INVOICE_FIELDS, ExtractedField, Record, Unreadable
from .values import ValueReader
from .vocabulary import FIELD_LABELS, TIER_WEIGHTS


def is_blank(cells: tuple) -> bool:
    return all(cell is None or str(cell).strip() == "" for cell in cells)


class TableLayout:
    """A sheet where every row below the header is one document."""

    def __init__(self, columns: ColumnMap, values: ValueReader | None = None) -> None:
        self._columns = columns
        self._values = values or ValueReader()

    def notes(self) -> tuple[Unreadable, ...]:
        """What the sheet lacks as a whole: it is the same for every row, so it is said once."""
        notes = []
        for name in INVOICE_FIELDS:
            if name in self._columns.columns:
                continue
            if name in self._columns.ambiguous:
                headers = " y ".join(f"'{header}'" for header in self._columns.ambiguous[name])
                notes.append(Unreadable(name, f"hay dos columnas posibles para {FIELD_LABELS[name]}: {headers}"))
            else:
                notes.append(Unreadable(name, f"la planilla no tiene columna de {FIELD_LABELS[name]}"))
        return tuple(notes)

    def records(self, rows: list[tuple]) -> tuple[Record, ...]:
        records = []
        for number, cells in enumerate(rows, start=1):
            if number <= self._columns.row or is_blank(cells):
                continue
            records.append(self._record(number, cells))
        return tuple(records)

    def _record(self, number: int, cells: tuple) -> Record:
        fields, unreadable = {}, []
        for name, column in self._columns.columns.items():
            raw = cells[column.index] if column.index < len(cells) else None
            reading = self._values.read(name, raw)
            source = f"columna '{column.header}', fila {number}"
            if reading.value is None:
                unreadable.append(Unreadable(name, reading.reason, record=number))
                continue
            fields[name] = ExtractedField(
                name=name,
                value=reading.value,
                raw=str(raw),
                confidence=reading.confidence * TIER_WEIGHTS[column.tier],
                source=source,
                method=reading.method,
                reason=reading.reason,
            )
        return Record(fields=fields, unreadable=tuple(unreadable), index=number)


class PairsLayout:
    """A sheet where each field is a label cell with its value in the next cell."""

    def __init__(self, matcher: HeaderMatcher | None = None, values: ValueReader | None = None) -> None:
        self._matcher = matcher or HeaderMatcher()
        self._values = values or ValueReader()

    def record(self, rows: list[tuple]) -> Record:
        found, rejected = self._candidates(rows)
        fields, unreadable = {}, []
        for name in INVOICE_FIELDS:
            readings = found.get(name, [])
            if not readings:
                reason = rejected.get(name) or f"no aparece {FIELD_LABELS[name]} en la planilla"
                unreadable.append(Unreadable(name, reason))
                continue
            if len({reading.value for _, _, reading in readings}) > 1:
                shown = ", ".join(sorted(f"'{raw}'" for _, raw, _ in readings))
                unreadable.append(Unreadable(name, f"hay mas de un valor posible para {FIELD_LABELS[name]}: {shown}"))
                continue
            where, raw, reading = readings[0]
            fields[name] = ExtractedField(
                name=name,
                value=reading.value,
                raw=str(raw),
                confidence=reading.confidence,
                source=f"celda {where}",
                method=reading.method,
                reason=reading.reason,
            )
        return Record(fields=fields, unreadable=tuple(unreadable))

    def _candidates(self, rows: list[tuple]) -> tuple[dict[str, list], dict[str, str]]:
        """Label cells with a value to their right. Only a literal label counts here: a
        loose cell of free text is not a header, so no fuzzy match is allowed."""
        found: dict[str, list] = {}
        rejected: dict[str, str] = {}
        for number, cells in enumerate(rows, start=1):
            for index, cell in enumerate(cells):
                if not isinstance(cell, str):
                    continue
                match = self._matcher.field_of(cell)
                if not match or match[1] < TOKEN:
                    continue
                at = next((i for i in range(index + 1, len(cells)) if not is_blank((cells[i],))), None)
                if at is None:
                    continue
                reading = self._values.read(match[0], cells[at])
                if reading.value is None:
                    rejected.setdefault(match[0], reading.reason)
                    continue
                where = f"{get_column_letter(at + 1)}{number}"
                found.setdefault(match[0], []).append((where, cells[at], reading))
        return found, rejected
