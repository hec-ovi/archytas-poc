"""Where the wording lives: one `.md` per rule, read at runtime.

Keeping the text out of the code is what lets someone rewrite an alert without touching
Python, and what keeps the WhatsApp wording (which Meta reviews) readable in one place.

File shape: the first line is the title, everything after it is the body. Both can carry
named placeholders like `{numero}`, filled by the rule.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .errors import MissingText

MESSAGES_DIR = Path(__file__).with_name("messages")


@dataclass(frozen=True)
class AlertText:
    """One alert already written out: a title and a body."""

    title: str
    body: str


class TextLibrary:
    """Loads and fills the alert texts. Reads each file once per process."""

    def __init__(self, folder: str | Path | None = None):
        self._folder = Path(folder) if folder else MESSAGES_DIR
        self._cache: dict[str, tuple[str, str]] = {}

    def render(self, name: str, params: Mapping[str, str]) -> AlertText:
        title, body = self._load(name)
        return AlertText(title=self._fill(title, params, name), body=self._fill(body, params, name))

    def _load(self, name: str) -> tuple[str, str]:
        if name not in self._cache:
            path = self._folder / f"{name}.md"
            if not path.is_file():
                raise MissingText(f"falta el texto {name}.md en {self._folder}")
            title, _, body = path.read_text(encoding="utf-8").strip().partition("\n")
            self._cache[name] = (title.strip(), body.strip())
        return self._cache[name]

    @staticmethod
    def _fill(text: str, params: Mapping[str, str], name: str) -> str:
        try:
            return text.format_map(params)
        except (KeyError, IndexError) as missing:
            raise MissingText(f"el texto {name}.md pide {missing} y la regla no lo paso") from missing
