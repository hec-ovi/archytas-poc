"""PDF pages to images, so OCR has something to look at.

Poppler's `pdftoppm` is the first choice because it renders the page as it prints. When it
is not on the machine, the page's embedded scan is pulled straight out of the PDF with
pypdf, which covers the usual case of a photographed invoice pasted into one page.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from pypdf import PdfReader

RENDER_TIMEOUT = 120


class PdfRasterizer:
    """Writes one image per page into `out_dir` and returns them in page order."""

    def __init__(self, dpi: int = 300, binary: str | None = None) -> None:
        self._dpi = dpi
        self._binary = binary

    @property
    def binary(self) -> str:
        """Where poppler lives. Overridable so a container can move it."""
        return self._binary or os.environ.get("PDFTOPPM_BIN", "pdftoppm")

    def render(self, pdf: Path, out_dir: Path) -> list[Path]:
        return self._with_poppler(pdf, out_dir) or self._embedded_images(pdf, out_dir)

    def _with_poppler(self, pdf: Path, out_dir: Path) -> list[Path]:
        binary = shutil.which(self.binary)
        if not binary:
            return []
        prefix = out_dir / "pagina"
        done = subprocess.run(
            [binary, "-r", str(self._dpi), "-png", str(pdf), str(prefix)],
            capture_output=True, timeout=RENDER_TIMEOUT, check=False,
        )
        return sorted(out_dir.glob("pagina-*.png")) if done.returncode == 0 else []

    @staticmethod
    def _embedded_images(pdf: Path, out_dir: Path) -> list[Path]:
        written = []
        for number, page in enumerate(PdfReader(str(pdf)).pages, start=1):
            for order, image in enumerate(page.images, start=1):
                target = out_dir / f"pagina-{number}-{order}-{image.name}"
                target.write_bytes(image.data)
                written.append(target)
        return written
