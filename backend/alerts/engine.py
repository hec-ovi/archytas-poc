"""One pass: decide, raise, send once, and retry what did not get out.

Four things keep this from becoming the inbox nobody reads. An event is raised once, by its
dedupe key, so the same due date is not announced every twelve hours. Only a new event is
sent. One invoice produces one alert per pass: if two rules speak about it, the one higher
in the priority order wins. And when a rule finds more than `aviso_maximo_por_regla` new
events at once, the events are still raised one by one, but what goes out is a single
digest: seventy four notifications is the tray the client already ignores, and every one of
them costs money to deliver.
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

DIGEST_DETAIL = "entregado dentro del resumen de la regla"


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

        self._retry_failed(settings, report)

        alerted: set[tuple[str | None, int]] = set()
        for rule in self._rules:
            fresh: list[tuple[int, AlertEvent]] = []
            for event in self._evaluate(rule, settings, report):
                if self._claimed(event, alerted):
                    report.skipped += 1
                    continue
                event_id, is_new = self._store.alerts.raise_event(event.as_row())
                if is_new:
                    report.raised += 1
                    fresh.append((event_id, event))
                else:
                    report.repeated += 1
            self._deliver(rule, fresh, None, settings, report)
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

    def _deliver(
        self,
        rule: Rule | None,
        batch: Sequence[tuple[int, AlertEvent]],
        recipients: Sequence[str] | None,
        settings: AlertSettings,
        report: AlertRun,
    ) -> None:
        """One message each, or one digest for all of them once they stop being readable."""
        if not batch:
            return

        digest = (
            rule.digest([event for _, event in batch])
            if rule is not None and len(batch) > settings.aviso_maximo_por_regla
            else None
        )
        if digest is None:
            for event_id, event in batch:
                self._send([event_id], event.as_message(), recipients, report)
            return

        report.digests += 1
        report.grouped += len(batch)
        self._send([event_id for event_id, _ in batch], digest, recipients, report, DIGEST_DETAIL)

    def _retry_failed(self, settings: AlertSettings, report: AlertRun) -> None:
        """Deliveries that failed go out again without the event firing a second time.

        Grouped by rule and passed through the same digest threshold, so a channel that was
        down while seventy events piled up does not turn into seventy messages on recovery.
        """
        pending: dict[int, set[str]] = {}
        for delivery in self._store.deliveries.failed():
            pending.setdefault(delivery["event_id"], set()).add(delivery["recipient"])

        batches: dict[str, list[tuple[int, AlertEvent]]] = {}
        recipients: dict[str, set[str]] = {}
        for event_id, targets in pending.items():
            stored = self._store.alerts.get(event_id)
            if stored is None:
                continue
            event = AlertEvent.from_row(stored)
            batches.setdefault(event.rule, []).append((event_id, event))
            recipients.setdefault(event.rule, set()).update(targets)
            report.retried += len(targets)

        known = {rule.name: rule for rule in self._rules}
        for rule_name, batch in batches.items():
            self._deliver(known.get(rule_name), batch, sorted(recipients[rule_name]), settings, report)

    def _send(
        self,
        event_ids: Sequence[int],
        message: Message,
        recipients: Sequence[str] | None,
        report: AlertRun,
        detail: str = "",
    ) -> None:
        """Send once, and record the outcome against every event the message carried."""
        for delivery in self._notifier.send(message, recipients):
            status = "entregado" if delivery.delivered else "fallido"
            for event_id in event_ids:
                self._store.deliveries.record(
                    event_id, delivery.channel, delivery.recipient, status, delivery.reason or detail
                )
            if delivery.delivered:
                report.delivered += 1
            else:
                report.failed += 1
