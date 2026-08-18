"""One pass: decide, raise, send once, and retry what did not get out.

Three things keep this from becoming the inbox nobody reads. An event is raised once, by its
dedupe key, so the same due date is not announced every twelve hours. Only a new event is
sent. And one invoice produces one alert per pass: if two rules speak about it, the one
higher in the priority order wins and the other is dropped.
"""

from __future__ import annotations

from typing import Iterable, Sequence

from notify import Message, Notifier
from store import Store

from .event import AlertEvent
from .report import AlertRun
from .rule import Rule
from .rules import default_rules
from .settings import AlertSettings
from .texts import TextLibrary


class AlertEngine:
    """Runs the rules against the database and gets the new ones delivered."""

    def __init__(
        self,
        store: Store,
        notifier: Notifier,
        rules: Iterable[Rule] | None = None,
        texts: TextLibrary | None = None,
    ):
        self._store = store
        self._notifier = notifier
        self._rules = tuple(rules) if rules is not None else tuple(default_rules(texts))

    @property
    def rules(self) -> tuple[str, ...]:
        return tuple(rule.name for rule in self._rules)

    def run(self, today: str | None = None) -> AlertRun:
        """Evaluate everything for `today` (the real date when it is not given)."""
        report = AlertRun()
        settings = AlertSettings.load(self._store, today)

        self._retry_failed(report)

        alerted: set[tuple[str | None, int]] = set()
        for rule in self._rules:
            for event in self._evaluate(rule, settings, report):
                if self._claimed(event, alerted):
                    report.skipped += 1
                    continue
                self._raise(event, report)
        return report

    def _evaluate(self, rule: Rule, settings: AlertSettings, report: AlertRun) -> list[AlertEvent]:
        try:
            return rule.evaluate(self._store, settings)
        except Exception as error:  # one broken rule must not silence the other five
            report.errors.append(f"la regla {rule.name} fallo: {error}")
            return []

    @staticmethod
    def _claimed(event: AlertEvent, alerted: set[tuple[str | None, int]]) -> bool:
        """True when a higher priority rule already spoke about this same thing."""
        if event.entity_id is None:
            return False
        key = (event.entity_kind, event.entity_id)
        if key in alerted:
            return True
        alerted.add(key)
        return False

    def _raise(self, event: AlertEvent, report: AlertRun) -> None:
        event_id, is_new = self._store.alerts.raise_event(event.as_row())
        if not is_new:
            report.repeated += 1
            return
        report.raised += 1
        self._send(event_id, event.as_message(), None, report)

    def _retry_failed(self, report: AlertRun) -> None:
        """Deliveries that failed go out again without the event firing a second time."""
        pending: dict[int, set[str]] = {}
        for delivery in self._store.deliveries.failed():
            pending.setdefault(delivery["event_id"], set()).add(delivery["recipient"])

        for event_id, recipients in pending.items():
            stored = self._store.alerts.get(event_id)
            if stored is None:
                continue
            report.retried += len(recipients)
            self._send(event_id, AlertEvent.from_row(stored).as_message(), sorted(recipients), report)

    def _send(
        self,
        event_id: int,
        message: Message,
        recipients: Sequence[str] | None,
        report: AlertRun,
    ) -> None:
        for delivery in self._notifier.send(message, recipients):
            self._store.deliveries.record(
                event_id,
                delivery.channel,
                delivery.recipient,
                "entregado" if delivery.delivered else "fallido",
                delivery.reason or "",
            )
            if delivery.delivered:
                report.delivered += 1
            else:
                report.failed += 1
