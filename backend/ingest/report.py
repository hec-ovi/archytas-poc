"""What one ingestion pass did, in a shape a person can read.

Counting is not decoration here. The client's whole complaint is that numbers appear without
anyone knowing where they came from, so every stage says what it took in, what it resolved
on its own, and what it refused to decide.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class StageReport:
    """One dataset's pass: how much came in, how much landed, how much needs a person."""

    name: str
    seen: int = 0
    stored: int = 0
    resolved: int = 0
    for_review: int = 0
    skipped: int = 0
    notes: list[str] = field(default_factory=list)

    def note(self, text: str) -> None:
        if text not in self.notes:
            self.notes.append(text)

    def as_dict(self) -> dict[str, Any]:
        return {
            "etapa": self.name,
            "leidos": self.seen,
            "guardados": self.stored,
            "resueltos": self.resolved,
            "a_revision": self.for_review,
            "salteados": self.skipped,
            "notas": self.notes,
        }


@dataclass
class IngestReport:
    """The whole pass."""

    stages: list[StageReport] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def stage(self, name: str) -> StageReport:
        report = StageReport(name=name)
        self.stages.append(report)
        return report

    @property
    def for_review(self) -> int:
        return sum(stage.for_review for stage in self.stages)

    @property
    def stored(self) -> int:
        return sum(stage.stored for stage in self.stages)

    def as_dict(self) -> dict[str, Any]:
        return {
            "etapas": [stage.as_dict() for stage in self.stages],
            "guardados": self.stored,
            "a_revision": self.for_review,
            "errores": self.errors,
        }
