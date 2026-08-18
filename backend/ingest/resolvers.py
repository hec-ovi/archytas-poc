"""Turning the names people typed into the entities that actually exist.

Suppliers and rubros have the same problem and two different solutions.

Suppliers have an authority: the account statements carry a CUIT, an email and a payment
term per supplier, and that is the real list. Everything else gets matched against it.

Rubros have no authority. Nobody ever wrote down the real list, so it has to be discovered
from the spellings themselves, and the fullest spelling of each group becomes the canonical
one.

Both remember what they learn. A spelling resolved once becomes an alias, so the next sync
resolves it instantly and a person is never asked the same question twice.
"""

from __future__ import annotations

from typing import Any

from normalizer.matching import CatalogEntry, CatalogMatcher, build_catalog, slugify
from normalizer.result import Normalized, resolved
from store import Store

SEPARATOR = "\x1f"

# The portal signs its own automatic warnings with this name. It is not a supplier, and
# treating it as one invents a ninth company out of thin air.
NOT_A_SUPPLIER = {"sistema sigprov", "sigprov", "sistema"}


class SupplierResolver:
    """Resolves a written supplier name to a real supplier id."""

    def __init__(self, store: Store):
        self._store = store
        self._matcher = CatalogMatcher()
        self._ids: dict[str, int] = {}
        self.reload()

    def reload(self) -> None:
        self._matcher = CatalogMatcher()
        self._ids = {}
        for row in self._store.supplier_aliases.catalog_rows():
            spellings = tuple(s for s in (row["spellings"] or "").split(SEPARATOR) if s)
            self._matcher.add(CatalogEntry(key=row["slug"], name=row["name"], aliases=spellings))
            self._ids[row["slug"]] = row["id"]

    def is_supplier(self, raw: str) -> bool:
        from normalizer.text import fold
        return fold(raw) not in NOT_A_SUPPLIER

    def resolve(self, raw: str) -> tuple[int | None, Normalized]:
        """Returns the supplier id and the result explaining how it got there."""
        if not raw or not raw.strip():
            from normalizer.result import unresolved
            return None, unresolved("", "sin proveedor")

        alias = self._store.supplier_aliases.resolve(raw.strip())
        if alias:
            return alias["supplier_id"], resolved(raw, alias["supplier_id"], "alias-conocido")

        match = self._matcher.match(raw)
        if match.resolved:
            supplier_id = self._ids.get(match.value)
            if supplier_id:
                # remembering it turns tomorrow's fuzzy match into an exact hit
                self._store.supplier_aliases.remember(supplier_id, raw.strip(), match.method, match.confidence)
                return supplier_id, match
        return None, match

    def id_for_slug(self, slug: str) -> int | None:
        return self._ids.get(slug)


class CategoryResolver:
    """Resolves a written rubro to a real rubro id, discovering the real list on the way."""

    def __init__(self, store: Store):
        self._store = store
        self._matcher = CatalogMatcher()
        self._ids: dict[str, int] = {}
        self.reload()

    def reload(self) -> None:
        self._matcher = CatalogMatcher()
        self._ids = {}
        for row in self._store.category_aliases.catalog_rows():
            spellings = tuple(s for s in (row["spellings"] or "").split(SEPARATOR) if s)
            self._matcher.add(CatalogEntry(key=row["slug"], name=row["name"], aliases=spellings))
            self._ids[row["slug"]] = row["id"]

    def discover(self, spellings: list[str]) -> dict[str, Any]:
        """Group every spelling seen into real rubros and store them with their aliases."""
        catalog = build_catalog(spellings)
        created = 0
        for entry in catalog.entries:
            category_id = self._store.categories.save({"slug": entry.key, "name": entry.name})
            created += 1
            self._store.category_aliases.remember(category_id, entry.name, "canonico")
            for alias in entry.aliases:
                self._store.category_aliases.remember(category_id, alias, "agrupado")
        self.reload()
        return {"escrituras": len(set(s for s in spellings if s.strip())), "rubros": created}

    def resolve(self, raw: str, subcategory: str = "") -> tuple[int | None, Normalized]:
        """Resolve a rubro, falling back to the subcategory when the rubro is blank.

        Eight products carry no rubro at all, and the client wants his spend broken down
        without a "leftovers" pile. The subcategory is always filled and maps cleanly onto
        one rubro, so a blank rubro is answerable instead of unknown.
        """
        if raw and raw.strip():
            match = self._matcher.match(raw)
            if match.resolved:
                category_id = self._ids.get(match.value)
                if category_id:
                    self._store.category_aliases.remember(category_id, raw.strip(), match.method, match.confidence)
                    return category_id, match
            return None, match

        if subcategory and subcategory.strip():
            inferred = self._store.db.one(
                """
                SELECT c.id, c.slug FROM product p
                JOIN category c ON c.id = p.category_id
                WHERE p.subcategory = ? AND p.category_id IS NOT NULL
                GROUP BY c.id ORDER BY COUNT(*) DESC LIMIT 1
                """,
                (subcategory.strip(),),
            )
            if inferred:
                return inferred["id"], resolved(raw or "", inferred["slug"], "por-subrubro", 0.95,
                                                f"sin rubro cargado, deducido de la subcategoria {subcategory!r}")

        from normalizer.result import unresolved
        return None, unresolved(raw or "", "producto sin rubro y sin subcategoria util")
