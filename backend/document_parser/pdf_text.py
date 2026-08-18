"""PDFs that carry their own text layer, which is most of what suppliers email.

pdfplumber gives the text as the page lays it out, line by line, which is what the field
labels need. A PDF whose text layer is thin is not this reader's problem: the parser sends
it to OCR instead.
"""

from __future__ import annotations

from pathlib import Path

import pdfplumber

from .errors import UnreadableFile
from .fields import FieldExtractor
from .result import READER_PDF_TEXT, ParseResult

# under this many characters there is no text layer worth reading
MIN_TEXT_CHARS = 20

ORIGIN = "texto del PDF"


class PdfTextReader:
    """One born digital PDF in, one `ParseResult` out."""

    def __init__(self, extractor: FieldExtractor | None = None) -> None:
        self._extractor = extractor or FieldExtractor()

    @staticmethod
    def has_text(text: str) -> bool:
        stripped = text.strip()
        return len(stripped) >= MIN_TEXT_CHARS and any(char.isalpha() for char in stripped)

    def extract_text(self, path: Path) -> str:
        try:
            with pdfplumber.open(path) as pdf:
                return "\n".join(page.extract_text() or "" for page in pdf.pages)
        except Exception as error:  # pdfminer raises its own family of errors
            raise UnreadableFile(f"no se pudo abrir el PDF: {error}") from error

    def read(self, path: Path, text: str | None = None) -> ParseResult:
        """`text` is passed in when the parser already extracted it to route the file."""
        body = self.extract_text(path) if text is None else text
        return ParseResult(
            source=path.name,
            kind=self._extractor.classify(body),
            reader=READER_PDF_TEXT,
            text=body,
            records=(self._extractor.extract(body, ORIGIN),),
        )
