"""Finding records that arrived more than once.

Two very different situations share the name "duplicate", and treating them the same is how
totals go wrong:

- the same record loaded twice, byte for byte. Safe to collapse: keep one, drop the rest.
- the same identifier carrying different content. Nobody can tell which one is true, so
  neither is counted and a person decides.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, Sequence


class DuplicateKind(str, Enum):
    IDENTICAL = "identical"   # collapse silently, keep the first
    CONFLICTING = "conflicting"  # hold all of them, ask a person


@dataclass(frozen=True)
class DuplicateGroup:
    """Every record that showed up under one identifier."""

    key: str
    kind: DuplicateKind
    rows: tuple[dict[str, Any], ...]
    differing_fields: tuple[str, ...] = ()

    @property
    def count(self) -> int:
        return len(self.rows)


class DuplicateFinder:
    """Groups rows by an identifier and says what kind of duplicate each group is."""

    def __init__(self, key_field: str, compare_fields: Sequence[str] | None = None):
        self._key_field = key_field
        self._compare_fields = tuple(compare_fields) if compare_fields else None

    def scan(self, rows: Iterable[dict[str, Any]]) -> list[DuplicateGroup]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            key = row.get(self._key_field)
            if key in (None, ""):
                continue
            grouped[str(key)].append(row)

        return [
            self._classify(key, group)
            for key, group in grouped.items()
            if len(group) > 1
        ]

    def _classify(self, key: str, group: list[dict[str, Any]]) -> DuplicateGroup:
        fields = self._compare_fields or self._fields_of(group)
        differing = tuple(
            field for field in fields
            if len({_hashable(row.get(field)) for row in group}) > 1
        )
        kind = DuplicateKind.IDENTICAL if not differing else DuplicateKind.CONFLICTING
        return DuplicateGroup(key=key, kind=kind, rows=tuple(group), differing_fields=differing)

    @staticmethod
    def _fields_of(group: list[dict[str, Any]]) -> tuple[str, ...]:
        seen: dict[str, None] = {}
        for row in group:
            seen.update(dict.fromkeys(row))
        return tuple(seen)


def _hashable(value: Any) -> Any:
    if isinstance(value, dict):
        return tuple(sorted((k, _hashable(v)) for k, v in value.items()))
    if isinstance(value, list):
        return tuple(_hashable(v) for v in value)
    return value
