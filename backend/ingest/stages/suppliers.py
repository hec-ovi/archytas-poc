"""Loading the real supplier list.

The account statements are the only place with a CUIT, an email, a phone and the agreed
payment term, so they are the authority. Everything downstream matches against what lands
here.

The movement ledger in those statements is deliberately not stored. It is a running balance
that can be recomputed exactly from the invoices and payments, and a stored copy of a
derived number is a copy that will eventually disagree.
"""

from __future__ import annotations

import re

from ingest.report import StageReport
from normalizer.money import parse_amount
from store import Store

TERM_DAYS = re.compile(r"(\d+)")


class SupplierStage:
    """Creates or updates the suppliers, with their contact details and their terms."""

    name = "proveedores"

    def __init__(self, store: Store):
        self._store = store

    def run(self, rows: list[dict], report: StageReport) -> None:
        report.seen = len(rows)
        for row in rows:
            slug = row.get("slug") or _slug(row.get("proveedor", ""))
            terms_raw = row.get("condicionPago") or ""
            match = TERM_DAYS.search(terms_raw)
            self._store.suppliers.save(
                {
                    "slug": slug,
                    "name": row.get("proveedor", "").strip(),
                    "cuit": row.get("cuit"),
                    "email": row.get("email"),
                    "phone": row.get("telefono"),
                    "address": row.get("domicilio"),
                    "terms_days": int(match.group(1)) if match else None,
                    "terms_raw": terms_raw,
                    "confirmed": 1,
                    "extra": {"saldo_portal": parse_amount(row.get("saldoActual")).value},
                }
            )
            report.stored += 1
            report.resolved += 1

        # the canonical spelling is itself an alias, so an exact name resolves without fuzzy work
        for supplier in self._store.suppliers.all():
            self._store.supplier_aliases.remember(supplier["id"], supplier["name"], "canonico")
        report.note("el saldo que publica el portal se guarda solo como referencia: el saldo real se calcula de facturas y pagos")


def _slug(name: str) -> str:
    from normalizer.matching import slugify
    return slugify(name)
