"""Finding the header row of a spreadsheet and mapping its columns to invoice fields.

The header is rarely on row 1: sheets arrive with a title, a logo row, or a blank line on
top. So the header is not assumed, it is looked for: the row that maps the most invoice
fields wins.

Two columns that name the same field with equal strength are not resolved by picking one.
The field is set aside as ambiguous and reported.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field

from normalizer.text import fold, similarity

from .vocabulary import COLUMN_KEYWORDS

# a row has to name at least this many invoice fields to be a header
MIN_FIELDS = 3

# how far down the sheet the header can hide
SEARCH_ROWS = 25

EXACT = 1.0
PHRASE = 0.9
TOKEN = 0.8
FUZZY = 0.7
FUZZY_THRESHOLD = 0.87


@dataclass(frozen=True)
class Column:
    """One spreadsheet column that names an invoice field."""

    field: str
    header: str
    index: int
    score: float

    @property
    def tier(self) -> int:
        """Fuzzy matches are tier 1, so what they produce needs a person to confirm."""
        return 0 if self.score >= TOKEN else 1


class HeaderMatcher:
    """One header cell to one invoice field, by the Spanish words that name it."""

    def field_of(self, header: object) -> tuple[str, float] | None:
        text = fold(str(header or ""))
        if not text:
            return None
        best: tuple[str, float] | None = None
        for name, keywords in COLUMN_KEYWORDS.items():
            score = max(self._score(text, keyword) for keyword in keywords)
            if score and (best is None or score > best[1]):
                best = (name, score)
        return best

    @staticmethod
    def _score(header: str, keyword: str) -> float:
        if header == keyword:
            return EXACT
        words, wanted = header.split(), keyword.split()
        for start in range(len(words) - len(wanted) + 1):
            if words[start:start + len(wanted)] == wanted:
                return PHRASE if len(wanted) > 1 else TOKEN
        # last chance for a typed header: "Fehca", "Proveedorr"
        return FUZZY if similarity(header, keyword) >= FUZZY_THRESHOLD else 0.0


@dataclass(frozen=True)
class ColumnMap:
    """The invoice columns of one header row, plus the ones left ambiguous."""

    row: int
    columns: dict[str, Column] = dc_field(default_factory=dict)
    ambiguous: dict[str, tuple[str, ...]] = dc_field(default_factory=dict)

    @property
    def size(self) -> int:
        return len(self.columns)

    @classmethod
    def of_row(cls, row_number: int, cells: tuple, matcher: HeaderMatcher) -> ColumnMap:
        found: dict[str, list[Column]] = {}
        for index, cell in enumerate(cells):
            match = matcher.field_of(cell)
            if match:
                name, score = match
                found.setdefault(name, []).append(Column(name, str(cell).strip(), index, score))

        columns, ambiguous = {}, {}
        for name, candidates in found.items():
            best = max(candidate.score for candidate in candidates)
            winners = [candidate for candidate in candidates if candidate.score == best]
            if len(winners) > 1:
                ambiguous[name] = tuple(candidate.header for candidate in winners)
            else:
                columns[name] = winners[0]
        return cls(row=row_number, columns=columns, ambiguous=ambiguous)

    @classmethod
    def find(cls, rows: list[tuple], matcher: HeaderMatcher) -> ColumnMap | None:
        """The best header row in the first rows of the sheet, or `None` if there is none."""
        best: ColumnMap | None = None
        for number, cells in enumerate(rows[:SEARCH_ROWS], start=1):
            candidate = cls.of_row(number, cells, matcher)
            if candidate.size >= MIN_FIELDS and (best is None or candidate.size > best.size):
                best = candidate
        return best
