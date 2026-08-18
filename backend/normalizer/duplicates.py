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
from typing import Any, Callable, Iterable, Sequence


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

    def __init__(
        self,
        key_field: str,
        compare_fields: Sequence[str] | None = None,
        key_normalizer: Callable[[Any], str] = None,
    ):
        self._key_field = key_field
        self._compare_fields = tuple(compare_fields) if compare_fields else None
        self._normalize_key = key_normalizer or normalize_key

    def scan(self, rows: Iterable[dict[str, Any]]) -> list[DuplicateGroup]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            key = self._normalize_key(row.get(self._key_field))
            if not key:
                continue
            grouped[key].append(row)

        return [
            self._classify(key, group)
            for key, group in grouped.items()
            if len(group) > 1
        ]

    def _classify(self, key: str, group: list[dict[str, Any]]) -> DuplicateGroup:
        # the identifier itself is excluded: rows grouped here already share it, and the
        # spelling it arrived in ("V-1189" against " v-1189 ") is noise, not a conflict
        fields = tuple(f for f in (self._compare_fields or self._fields_of(group)) if f != self._key_field)
        differing = tuple(
            field for field in fields
            if len({_hashable(_trim(row.get(field))) for row in group}) > 1
        )
        kind = DuplicateKind.IDENTICAL if not differing else DuplicateKind.CONFLICTING
        return DuplicateGroup(key=key, kind=kind, rows=tuple(group), differing_fields=differing)

    @staticmethod
    def _fields_of(group: list[dict[str, Any]]) -> tuple[str, ...]:
        seen: dict[str, None] = {}
        for row in group:
            seen.update(dict.fromkeys(row))
        return tuple(seen)


def normalize_key(value: Any) -> str:
    """The identifier as identity, not as typed.

    The same sale code arrives as `"V-1189"` and as `" v-1189 "`. Grouping on the literal
    string misses more than a third of the repeats, and those rows get counted twice.
    """
    if value is None:
        return ""
    return " ".join(str(value).split()).upper()


def _trim(value: Any) -> Any:
    """Surrounding whitespace is how a value was typed, not what it means."""
    return value.strip() if isinstance(value, str) else value


def _hashable(value: Any) -> Any:
    if isinstance(value, dict):
        return tuple(sorted((k, _hashable(v)) for k, v in value.items()))
    if isinstance(value, list):
        return tuple(_hashable(v) for v in value)
    return value
