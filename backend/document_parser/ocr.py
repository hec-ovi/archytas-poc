"""Tesseract, and what to do when it is not there.

The container ships tesseract with the Spanish pack. A developer machine often does not,
and that must not crash anything: `available` answers before any work starts, and the box
reports the missing engine as a note on the result.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytesseract

DEFAULT_LANGUAGE = "spa"


class TesseractEngine:
    """Reads text off an image. Resolves the binary on every call, so the environment wins."""

    def __init__(self, language: str = DEFAULT_LANGUAGE, binary: str | None = None) -> None:
        self._language = language
        self._binary = binary

    @property
    def binary(self) -> str:
        return self._binary or os.environ.get("TESSERACT_BIN", "tesseract")

    @property
    def available(self) -> bool:
        return shutil.which(self.binary) is not None

    def text(self, image: Path) -> str:
        """The text of one image. Raises `pytesseract.TesseractError` if the run fails."""
        pytesseract.pytesseract.tesseract_cmd = shutil.which(self.binary) or self.binary
        return pytesseract.image_to_string(str(image), lang=self._language)
