"""Raising a review item the same way every time.

Every stage needs to say "I could not decide this". Doing it through one place means the
queue reads consistently and the same doubt raised twice does not become two rows.
"""

from __future__ import annotations

from typing import Any

from normalizer.result import Normalized
from store import Store


class ReviewQueue:
    """Opens items in the review queue, and never opens the same one twice."""

    def __init__(self, store: Store):
        self._store = store

    def unresolved_value(self, kind: str, title: str, detail: str, raw: dict[str, Any],
                         result: Normalized, entity_kind: str = "", entity_id: int | None = None) -> int:
        """A value the normalizer refused to settle, with the candidates it did find."""
        return self._store.reviews.raise_item(
            {
                "kind": kind,
                "dedupe_key": f"{kind}:{result.raw}",
                "title": title,
                "detail": detail or result.reason,
                "raw": raw,
                "candidates": [{"valor": value, "puntaje": round(score, 3)} for value, score in result.candidates],
                "entity_kind": entity_kind,
                "entity_id": entity_id,
            }
        )

    def conflict(self, kind: str, key: str, title: str, detail: str, raw: dict[str, Any],
                 candidates: list[dict[str, Any]]) -> int:
        """Records that disagree with each other, where picking one is a business call."""
        return self._store.reviews.raise_item(
            {
                "kind": kind,
                "dedupe_key": f"{kind}:{key}",
                "title": title,
                "detail": detail,
                "raw": raw,
                "candidates": candidates,
            }
        )
