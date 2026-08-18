"""The way in: a file, and what could be read out of it.

Routing is by content, not by name. A PDF is tried as text first and sent to OCR only when
its text layer turns out to be empty, which is the honest way to tell a born digital
invoice from a photographed one.
"""

from __future__ import annotations

from pathlib import Path

from .errors import UnreadableFile, UnsupportedFormat
from .pdf_text import PdfTextReader
from .result import ParseResult
from .scanned import ScannedPdfReader
from .sniff import FORMAT_PDF, FORMAT_SPREADSHEET, FileSniffer
from .spreadsheet import SpreadsheetReader


class DocumentParser:
    """One file in, one `ParseResult` out. Readers are injectable for testing."""

    def __init__(
        self,
        pdf: PdfTextReader | None = None,
        scanned: ScannedPdfReader | None = None,
        spreadsheet: SpreadsheetReader | None = None,
        sniffer: FileSniffer | None = None,
    ) -> None:
        self._pdf = pdf or PdfTextReader()
        self._scanned = scanned or ScannedPdfReader()
        self._spreadsheet = spreadsheet or SpreadsheetReader()
        self._sniffer = sniffer or FileSniffer()

    def parse(self, path: str | Path) -> ParseResult:
        target = Path(path)
        if not target.is_file():
            raise UnreadableFile(f"no existe el archivo {target.name or path}")

        found = self._sniffer.format_of(target)
        if found == FORMAT_SPREADSHEET:
            return self._spreadsheet.read(target)
        if found == FORMAT_PDF:
            return self._read_pdf(target)
        raise UnsupportedFormat(f"{target.name} no es un PDF ni una planilla xlsx")

    def _read_pdf(self, path: Path) -> ParseResult:
        text = self._pdf.extract_text(path)
        if self._pdf.has_text(text):
            return self._pdf.read(path, text=text)
        return self._scanned.read(path)
