"""PDFs with no text layer: a photo or a scan of an invoice.

The page is rendered to an image and passed to tesseract in Spanish. Everything read this
way is worth a little less than a text layer, because OCR misreads digits, so every field
carries the OCR discount and lands closer to the review threshold.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from .fields import FieldExtractor
from .ocr import TesseractEngine
from .raster import PdfRasterizer
from .result import KIND_UNKNOWN, READER_OCR, ParseResult, Unreadable

# OCR reads well but not perfectly: a clean date stays applicable, anything already in
# doubt drops under the review line
OCR_WEIGHT = 0.95

ORIGIN = "OCR"


class ScannedPdfReader:
    """One scanned PDF in, one `ParseResult` out. Never raises for a missing engine."""

    def __init__(
        self,
        rasterizer: PdfRasterizer | None = None,
        engine: TesseractEngine | None = None,
        extractor: FieldExtractor | None = None,
    ) -> None:
        self._rasterizer = rasterizer or PdfRasterizer()
        self._engine = engine or TesseractEngine()
        self._extractor = extractor or FieldExtractor(weight=OCR_WEIGHT)

    def read(self, path: Path) -> ParseResult:
        if not self._engine.available:
            return self._empty(path, (
                f"el PDF no tiene texto y tesseract no esta instalado (se busco '{self._engine.binary}'), "
                "asi que no se pudo leer nada",
            ))

        with tempfile.TemporaryDirectory(prefix="document_parser-") as workspace:
            images = self._rasterizer.render(path, Path(workspace))
            if not images:
                return self._empty(path, ("no se pudo convertir el PDF en imagenes para leerlo",))
            text, failures = self._read_images(images)

        if not text.strip():
            return self._empty(path, failures or ("el OCR no encontro texto en el PDF",))

        record = self._extractor.extract(text, ORIGIN)
        return ParseResult(
            source=path.name,
            kind=self._extractor.classify(text),
            reader=READER_OCR,
            text=text,
            records=(record,),
            notes=tuple(Unreadable("documento", reason) for reason in failures),
        )

    def _read_images(self, images: list[Path]) -> tuple[str, tuple[str, ...]]:
        pages, failures = [], []
        for number, image in enumerate(images, start=1):
            try:
                pages.append(self._engine.text(image))
            except Exception as error:  # pytesseract wraps several failure shapes
                failures.append(f"el OCR fallo en la pagina {number}: {error}")
        return "\n".join(pages), tuple(failures)

    def _empty(self, path: Path, reasons: tuple[str, ...]) -> ParseResult:
        """Nothing was read. The record still lists the six fields, each with its reason."""
        return ParseResult(
            source=path.name,
            kind=KIND_UNKNOWN,
            reader=READER_OCR,
            text="",
            records=(self._extractor.extract("", ORIGIN),),
            notes=tuple(Unreadable("documento", reason) for reason in reasons),
        )
