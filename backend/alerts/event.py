"""One thing worth interrupting a person for.

The event is what the rule decided; sending it is somebody else's job. It carries its own
dedupe key, which is what stops the same due date from being announced every twelve hours.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from notify import Message, Template

AVISO = "aviso"
URGENTE = "urgente"


@dataclass(frozen=True)
class AlertEvent:
    """What a rule wants raised, in the shape the store and the notifier both accept."""

    rule: str
    dedupe_key: str
    severity: str
    title: str
    body: str
    entity_kind: str | None = None
    entity_id: int | None = None
    due_on: str | None = None
    params: Mapping[str, str] = field(default_factory=dict)
    template: str = ""

    def as_row(self) -> dict[str, Any]:
        return {
            "rule": self.rule,
            "dedupe_key": self.dedupe_key,
            "severity": self.severity,
            "title": self.title,
            "body": self.body,
            "entity_kind": self.entity_kind,
            "entity_id": self.entity_id,
            "due_on": self.due_on,
            "extra": {"parametros": dict(self.params), "plantilla": self.template},
        }

    def as_message(self) -> Message:
        """The same alert as plain text for any channel, and as a template for WhatsApp."""
        template = Template(name=self.template, params=dict(self.params)) if self.template else None
        return Message(text=f"{self.title}\n\n{self.body}", template=template)

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "AlertEvent":
        """Rebuild a stored event so a failed delivery can be retried with the same words."""
        extra = row.get("extra") or {}
        return cls(
            rule=row["rule"],
            dedupe_key=row["dedupe_key"],
            severity=row["severity"],
            title=row["title"],
            body=row["body"],
            entity_kind=row.get("entity_kind"),
            entity_id=row.get("entity_id"),
            due_on=row.get("due_on"),
            params=extra.get("parametros", {}),
            template=extra.get("plantilla", ""),
        )
