"""What every normalizer returns.

A normalizer never guesses silently. It either resolves a raw value with a confidence, or
hands back a result that says "look at this", optionally with the best candidate it found
so a human only has to confirm.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# below this the value is not applied on its own, it goes to the review queue
REVIEW_THRESHOLD = 0.90


@dataclass(frozen=True)
class Normalized:
    """One raw value turned into a canonical one, with how sure we are and why."""

    raw: str
    value: Any = None
    confidence: float = 0.0
    method: str = "unresolved"
    reason: str = ""
    candidates: tuple[tuple[Any, float], ...] = field(default_factory=tuple)

    @property
    def resolved(self) -> bool:
        return self.value is not None and self.confidence >= REVIEW_THRESHOLD

    @property
    def needs_review(self) -> bool:
        return not self.resolved

    def as_dict(self) -> dict[str, Any]:
        return {
            "raw": self.raw,
            "value": self.value,
            "confidence": round(self.confidence, 4),
            "method": self.method,
            "reason": self.reason,
            "candidates": [{"value": v, "score": round(s, 4)} for v, s in self.candidates],
        }


def resolved(raw: str, value: Any, method: str, confidence: float = 1.0, reason: str = "") -> Normalized:
    return Normalized(raw=raw, value=value, confidence=confidence, method=method, reason=reason)


def unresolved(raw: str, reason: str, candidates: tuple[tuple[Any, float], ...] = ()) -> Normalized:
    return Normalized(raw=raw, value=None, confidence=0.0, method="unresolved", reason=reason, candidates=candidates)
