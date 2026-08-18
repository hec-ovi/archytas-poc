"""What every rule is, and the one question it answers.

A rule reads the database, decides, and hands back events. It never sends and never writes,
so it can be judged on its own: given these rows and these settings, does it interrupt?
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Mapping

from normalizer.money import format_amount
from store import Store

from .event import AVISO, AlertEvent
from .settings import AlertSettings
from .texts import TextLibrary


class Rule(ABC):
    """One reason to interrupt someone, with its wording in `messages/<text>.md`."""

    name: str = ""
    severity: str = AVISO
    text: str = ""
    entity_kind: str | None = None

    def __init__(self, texts: TextLibrary | None = None):
        self._texts = texts or TextLibrary()

    @abstractmethod
    def evaluate(self, store: Store, settings: AlertSettings) -> list[AlertEvent]:
        """The events this rule wants raised right now."""

    def _event(
        self,
        key: str,
        params: Mapping[str, str],
        entity_id: int | None = None,
        due_on: str | None = None,
    ) -> AlertEvent:
        written = self._texts.render(self.text, params)
        return AlertEvent(
            rule=self.name,
            dedupe_key=f"{self.name}:{key}",
            severity=self.severity,
            title=written.title,
            body=written.body,
            entity_kind=self.entity_kind,
            entity_id=entity_id,
            due_on=due_on,
            params=dict(params),
            template=self.text,
        )

    @staticmethod
    def money(cents: int | None, fallback: str = "sin estimar") -> str:
        return fallback if cents is None else format_amount(int(cents))

    @staticmethod
    def words(value: str | None, fallback: str) -> str:
        return str(value).strip() if value and str(value).strip() else fallback
