"""Reading an .xlsx workbook.

Invoices arrive as spreadsheets in two shapes and both are messy: the header row is not
always the first row, there are blank rows in the middle, and a column can be named in any
of a dozen ways. The reader tries the table shape first, then the label and value shape,
and if neither gives anything it says so instead of inventing rows.
"""

from __future__ import annotations

from pathlib import Path

import openpyxl

from .errors import UnreadableFile
from .fields import FieldExtractor
from .headers import ColumnMap, HeaderMatcher
from .layouts import PairsLayout, TableLayout, is_blank
from .result import (
    KIND_TABLE,
    KIND_UNKNOWN,
    READER_SPREADSHEET,
    ParseResult,
    Unreadable,
)


class SpreadsheetReader:
    """One workbook in, one `ParseResult` out."""

    def __init__(self, matcher: HeaderMatcher | None = None, extractor: FieldExtractor | None = None) -> None:
        self._matcher = matcher or HeaderMatcher()
        self._extractor = extractor or FieldExtractor()

    def read(self, path: Path) -> ParseResult:
        rows, sheet, extra_sheets = self._rows(path)
        text = self._as_text(rows)
        notes = list(extra_sheets)

        columns = ColumnMap.find(rows, self._matcher)
        if columns is not None:
            table = TableLayout(columns)
            notes.extend(table.notes())
            return ParseResult(
                source=path.name,
                kind=KIND_TABLE,
                reader=READER_SPREADSHEET,
                text=text,
                records=table.records(rows),
                notes=tuple(notes),
            )

        record = PairsLayout(self._matcher).record(rows)
        if not record.fields:
            notes.append(Unreadable(
                "documento",
                f"la hoja '{sheet}' no tiene columnas ni etiquetas de factura reconocibles",
            ))
            kind = KIND_UNKNOWN
        else:
            kind = self._extractor.classify(text)
        return ParseResult(
            source=path.name,
            kind=kind,
            reader=READER_SPREADSHEET,
            text=text,
            records=(record,),
            notes=tuple(notes),
        )

    def _rows(self, path: Path) -> tuple[list[tuple], str, list[Unreadable]]:
        try:
            book = openpyxl.load_workbook(path, data_only=True, read_only=True)
        except Exception as error:  # openpyxl raises half a dozen different things
            raise UnreadableFile(f"no se pudo abrir la planilla: {error}") from error

        try:
            sheet = book.worksheets[0]
            rows = [tuple(row) for row in sheet.iter_rows(values_only=True)]
            notes = []
            if len(book.worksheets) > 1:
                others = ", ".join(other.title for other in book.worksheets[1:])
                notes.append(Unreadable(
                    "documento",
                    f"la planilla tiene mas hojas y solo se leyo '{sheet.title}'. Sin leer: {others}",
                ))
            return rows, sheet.title, notes
        finally:
            book.close()

    @staticmethod
    def _as_text(rows: list[tuple]) -> str:
        """The sheet as plain text, so a person can see what the box saw."""
        lines = []
        for cells in rows:
            if is_blank(cells):
                continue
            lines.append("\t".join("" if cell is None else str(cell) for cell in cells).rstrip())
        return "\n".join(lines)
