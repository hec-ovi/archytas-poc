"""What one pass did, in a shape a person can read on screen."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AlertRun:
    """Counts for one pass: what fired, what was already known, and what got out."""

    raised: int = 0
    repeated: int = 0
    skipped: int = 0
    delivered: int = 0
    failed: int = 0
    retried: int = 0
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "eventos_nuevos": self.raised,
            "eventos_repetidos": self.repeated,
            "eventos_salteados": self.skipped,
            "entregas": self.delivered,
            "entregas_fallidas": self.failed,
            "reintentos": self.retried,
            "errores": self.errors,
        }
