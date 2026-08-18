"""What every rule is, and the two questions it answers.

A rule reads the database, decides, and hands back events. It never sends and never writes,
so it can be judged on its own: given these rows and these settings, does it interrupt?

The second question is what to say when it finds more than a person can read. That is the
digest: one message for the whole pile, named after the worst of them.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Mapping, Sequence

from normalizer.money import format_amount
from notify import Message, Template
from store import Store

from .event import AVISO, AlertEvent
from .settings import AlertSettings
from .texts import TextLibrary


class Rule(ABC):
    """One reason to interrupt someone, with its wording in `messages/<text>.md`."""

    name: str = ""
    severity: str = AVISO
    text: str = ""
    digest_text: str = ""
    entity_kind: str | None = None

    def __init__(self, texts: TextLibrary | None = None):
        self._texts = texts or TextLibrary()

    @abstractmethod
    def evaluate(self, store: Store, settings: AlertSettings) -> list[AlertEvent]:
        """The events this rule wants raised right now."""

    def digest(self, events: Sequence[AlertEvent]) -> Message | None:
        """One message for many events, or nothing when this rule never piles up.

        The text is filled with the parameters of the worst event (the highest `rank`), plus
        how many there are and what they add up to, so the wording stays in the `.md`.
        """
        if not self.digest_text or not events:
            return None
        worst = max(events, key=lambda event: event.rank)
        available = {
            **worst.params,
            "cantidad": str(len(events)),
            "total": format_amount(sum(event.amount_cents for event in events)),
        }
        params = {field: available.get(field, "") for field in self._texts.fields(self.digest_text)}
        written = self._texts.render(self.digest_text, params)
        return Message(
            text=f"{written.title}\n\n{written.body}",
            template=Template(name=self.digest_text, params=params),
        )

    def _event(
        self,
        key: str,
        params: Mapping[str, str],
        entity_id: int | None = None,
        due_on: str | None = None,
        amount_cents: int = 0,
        rank: int = 0,
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
            amount_cents=amount_cents,
            rank=rank,
        )

    @staticmethod
    def money(cents: int | None, fallback: str = "sin estimar") -> str:
        return fallback if cents is None else format_amount(int(cents))

    @staticmethod
    def words(value: str | None, fallback: str) -> str:
        return str(value).strip() if value and str(value).strip() else fallback
