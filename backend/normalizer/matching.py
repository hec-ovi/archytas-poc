"""Matching a messy string against a catalog of known entities.

Used for supplier names and for product categories. Both have the same shape: a small set
of real entities, and a much larger set of ways people spelled them.

Three outcomes, and the middle one is the point of the whole box:

- a confident match, applied on its own
- a likely match below the bar, sent to review with the candidate attached so a person
  confirms with one click
- nothing close, sent to review as a possible new entity
"""

from __future__ import annotations

from dataclasses import dataclass

from .result import Normalized, resolved, unresolved
from .text import fold, signature, similarity

STRONG = 0.90   # applied without asking
LIKELY = 0.72   # proposed, needs a person to confirm


@dataclass(frozen=True)
class CatalogEntry:
    """One real entity, with every spelling already known to mean it."""

    key: str
    name: str
    aliases: tuple[str, ...] = ()

    def spellings(self) -> tuple[str, ...]:
        return (self.name, *self.aliases)


class CatalogMatcher:
    """Resolves raw strings to catalog keys, and remembers what it learned."""

    def __init__(self, entries: list[CatalogEntry] | None = None):
        self._entries: dict[str, CatalogEntry] = {}
        self._by_signature: dict[str, str] = {}
        self._by_fold: dict[str, str] = {}
        for entry in entries or []:
            self.add(entry)

    def add(self, entry: CatalogEntry) -> None:
        self._entries[entry.key] = entry
        for spelling in entry.spellings():
            self._by_fold.setdefault(fold(spelling), entry.key)
            self._by_signature.setdefault(signature(spelling), entry.key)

    def learn_alias(self, key: str, spelling: str) -> None:
        """Record a spelling a person confirmed, so it resolves instantly next time."""
        entry = self._entries[key]
        self._entries[key] = CatalogEntry(entry.key, entry.name, (*entry.aliases, spelling))
        self._by_fold[fold(spelling)] = key
        self._by_signature[signature(spelling)] = key

    @property
    def entries(self) -> list[CatalogEntry]:
        return list(self._entries.values())

    def match(self, raw: str) -> Normalized:
        if not raw or not raw.strip():
            return unresolved("", "empty value")

        exact = self._by_fold.get(fold(raw))
        if exact:
            return resolved(raw, exact, "exact")

        same_signature = self._by_signature.get(signature(raw))
        if same_signature:
            return resolved(raw, same_signature, "signature", 0.98)

        scored = sorted(
            ((key, self._best_score(raw, entry)) for key, entry in self._entries.items()),
            key=lambda pair: pair[1],
            reverse=True,
        )
        if not scored:
            return unresolved(raw, "catalog is empty")

        best_key, best_score = scored[0]
        candidates = tuple((key, score) for key, score in scored[:3] if score >= LIKELY / 2)

        if best_score >= STRONG:
            return resolved(raw, best_key, "fuzzy", best_score)
        if best_score >= LIKELY:
            return unresolved(raw, f"looks like {best_key} but not close enough to apply", candidates)
        return unresolved(raw, "no known entity resembles this", candidates)

    @staticmethod
    def _best_score(raw: str, entry: CatalogEntry) -> float:
        return max(similarity(raw, spelling) for spelling in entry.spellings())


def build_catalog(values: list[str], threshold: float = STRONG) -> CatalogMatcher:
    """Derive a catalog from raw values, when nobody ever wrote down the real list.

    Supplier names have an authority to match against (the account statements carry CUIT and
    a canonical name). Product categories have none: the client typed them freely for years.
    So the real rubros have to be discovered from the spellings themselves.

    Values are grouped by similarity, and each group keeps its most complete spelling as the
    canonical one, on the reasoning that abbreviations are shortenings of a full name that
    someone, at some point, wrote out.
    """
    groups: list[list[str]] = []
    for value in sorted({v.strip() for v in values if v and v.strip()}, key=len, reverse=True):
        for group in groups:
            if any(similarity(value, member) >= threshold for member in group):
                group.append(value)
                break
        else:
            groups.append([value])

    matcher = CatalogMatcher()
    for group in groups:
        canonical = max(group, key=lambda v: (len(tokens_of(v)), len(v)))
        matcher.add(CatalogEntry(key=slugify(canonical), name=canonical, aliases=tuple(g for g in group if g != canonical)))
    return matcher


def tokens_of(value: str) -> list[str]:
    from .text import tokens
    return tokens(value)


def slugify(value: str) -> str:
    return "-".join(fold(value).split()) or "sin-nombre"
