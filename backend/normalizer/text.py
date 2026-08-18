"""Text cleanup shared by the matchers.

Everything here is deterministic: strip accents, drop legal suffixes and punctuation, and
compare token sets. No model involved.
"""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher

# "S.R.L.", "SRL", "S.A.", "SA", "SAS", "SACIF" and friends carry no identity
LEGAL_SUFFIXES = {
    "srl", "sa", "sas", "sacif", "saci", "sca", "scs", "sh", "ltda", "ltd", "inc",
    "cia", "y", "e", "hijos", "hnos", "hermanos",
}

# words people abbreviate when they get tired of typing
ABBREVIATIONS = {
    "distrib": "distribuidora",
    "dist": "distribuidora",
    "distr": "distribuidora",
    "ind": "industrial",
    "indust": "industrial",
    "insum": "insumos",
    "herram": "herramientas",
    "hrram": "herramientas",
    "ferr": "ferreteria",
    "mat": "materiales",
    "gral": "general",
    "grl": "general",
    "prod": "productos",
    "com": "comercial",
    "elec": "electricas",
    "electr": "electricas",
    "san": "sanitarios",
    "canerias": "canerias",
}


def strip_accents(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def fold(value: str) -> str:
    """Lowercase, accent-free, punctuation-free, single-spaced."""
    folded = strip_accents(value or "").lower()
    folded = re.sub(r"[^a-z0-9\s]", " ", folded)
    return re.sub(r"\s+", " ", folded).strip()


def tokens(value: str) -> list[str]:
    """Folded tokens with abbreviations expanded and legal suffixes dropped."""
    out = []
    for token in fold(value).split():
        token = ABBREVIATIONS.get(token, token)
        if token in LEGAL_SUFFIXES or len(token) < 2:
            continue
        out.append(token)
    return out


def signature(value: str) -> str:
    """A stable key: identity tokens, sorted. Two spellings of one name share it."""
    return " ".join(sorted(set(tokens(value))))


def similarity(left: str, right: str) -> float:
    """0..1 blend of token overlap and character similarity.

    Token overlap catches reordering and missing words; character similarity catches
    typos inside a word. The blend keeps a single typo from tanking the score while a
    genuinely different name still scores low.
    """
    left_tokens, right_tokens = set(tokens(left)), set(tokens(right))
    if not left_tokens or not right_tokens:
        return 0.0

    overlap = len(left_tokens & right_tokens) / len(left_tokens | right_tokens)
    chars = SequenceMatcher(None, signature(left), signature(right)).ratio()
    fuzzy_tokens = _best_token_alignment(left_tokens, right_tokens)
    return max(0.6 * overlap + 0.4 * chars, fuzzy_tokens * 0.95)


def _best_token_alignment(left: set[str], right: set[str]) -> float:
    """Average of each left token's best match on the right, and the other way round."""
    def one_way(source: set[str], target: set[str]) -> float:
        return sum(
            max(SequenceMatcher(None, item, other).ratio() for other in target)
            for item in source
        ) / len(source)

    return min(one_way(left, right), one_way(right, left))
