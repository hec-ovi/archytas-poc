"""What a file actually is.

The extension lies often enough to be useless on its own: a scan saved as `.pdf.xlsx`, a
`.xls` that is really an xlsx, an email attachment renamed by hand. So the first bytes
decide, and the extension is never consulted.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

from .errors import UnreadableFile

FORMAT_PDF = "pdf"
FORMAT_SPREADSHEET = "xlsx"

PDF_MAGIC = b"%PDF"
ZIP_MAGIC = b"PK\x03\x04"
WORKBOOK_ENTRY = "xl/workbook.xml"
HEAD_BYTES = 1024


class FileSniffer:
    """Reads the head of a file and names its format, or `None` if it is neither."""

    def format_of(self, path: Path) -> str | None:
        head = self._head(path)
        if head.startswith(PDF_MAGIC) or PDF_MAGIC in head:
            return FORMAT_PDF
        if head.startswith(ZIP_MAGIC) and self._is_workbook(path):
            return FORMAT_SPREADSHEET
        return None

    @staticmethod
    def _head(path: Path) -> bytes:
        try:
            with path.open("rb") as handle:
                head = handle.read(HEAD_BYTES)
        except OSError as error:
            raise UnreadableFile(f"no se pudo abrir el archivo: {error}") from error
        if not head:
            raise UnreadableFile("el archivo esta vacio")
        return head

    @staticmethod
    def _is_workbook(path: Path) -> bool:
        """A .docx is a zip too. Only a zip carrying a workbook part is a spreadsheet."""
        try:
            with zipfile.ZipFile(path) as archive:
                return WORKBOOK_ENTRY in archive.namelist()
        except zipfile.BadZipFile:
            return False
