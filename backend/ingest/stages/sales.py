"""Loading sales, and refusing to count the ones that cannot be trusted.

This is the stage the client described most precisely: "there are sales loaded twice by
mistake, and others with broken data; we need to be told which ones, not have them added up
as if they were valid."

Three things happen, in this order.

**Duplicates.** The same code arrives as `"V-1189"` and as `" v-1189 "`, so grouping on the
literal string misses more than a third of them. Grouped on identity, a repeat is either the
same row twice, which collapses on its own, or the same code with different quantities,
which nobody can settle from the data and goes to a person.

**Arithmetic gaps.** Quantity times unit price equals total is a closed identity. When
exactly one of the three is missing and the other two are there, the missing one is not a
guess, it is the only value it can be, and it is filled in with a note saying so.

**Real breakage.** A total that disagrees with a quantity and a price that are both present,
a date that does not exist, a product that is not in the catalogue: these are not repairable
by arithmetic. The row is kept, marked, left out of every total, and listed with a proposal
attached so a person can settle it in one click.
"""

from __future__ import annotations

import hashlib
import json

from ingest.report import StageReport
from ingest.review_queue import ReviewQueue
from normalizer.dates import parse_date
from normalizer.duplicates import DuplicateFinder, DuplicateKind, normalize_key
from normalizer.money import parse_amount
from store import Store

COMPARE_FIELDS = ("fecha", "productoId", "cliente", "cantidad", "precioUnit", "total")


class SaleStage:
    name = "ventas"

    def __init__(self, store: Store, review: ReviewQueue):
        self._store = store
        self._review = review

    def run(self, rows: list[dict], report: StageReport) -> None:
        report.seen = len(rows)
        conflicting = self._flag_conflicts(rows, report)
        collapsed: set[str] = set()

        for row in rows:
            code = normalize_key(row.get("codigo"))
            if not code:
                report.skipped += 1
                continue

            parsed = self._parse(row)
            status, note = self._verdict(code, parsed, conflicting)

            # an identical repeat adds nothing: the row hash makes the second one land on
            # the first instead of next to it
            fingerprint = _fingerprint(parsed)
            if status == "valida" and fingerprint in collapsed:
                continue
            collapsed.add(fingerprint)

            self._store.sales.save(
                {
                    "code": code,
                    "sold_on": parsed["sold_on"],
                    "product_id": parsed["product_id"],
                    "customer": parsed["customer"],
                    "quantity": parsed["quantity"],
                    "unit_cents": parsed["unit_cents"],
                    "total_cents": parsed["total_cents"],
                    "status": status,
                    "status_note": note,
                    "row_hash": fingerprint,
                    "extra": {"crudo": row, "reparaciones": parsed["repairs"]},
                }
            )
            report.stored += 1
            if status == "valida":
                report.resolved += 1
            else:
                report.for_review += 1

        health = self._store.sales.health()
        excluded = sum(v["count"] for k, v in health.items() if k != "valida")
        report.note(
            f"{health.get('valida', {}).get('count', 0)} ventas se pueden sumar, "
            f"{excluded} quedan afuera y estan listadas con el motivo"
        )

    # ------------------------------------------------------------------ duplicates

    def _flag_conflicts(self, rows: list[dict], report: StageReport) -> dict[str, list[dict]]:
        groups = DuplicateFinder("codigo", COMPARE_FIELDS).scan(rows)
        identical = [g for g in groups if g.kind is DuplicateKind.IDENTICAL]
        conflicting = {g.key: list(g.rows) for g in groups if g.kind is DuplicateKind.CONFLICTING}

        for group in conflicting.values():
            code = normalize_key(group[0].get("codigo"))
            self._review.conflict(
                kind="venta-duplicada",
                key=code,
                title=f"La venta {code} figura {len(group)} veces con datos distintos",
                detail="Las filas coinciden en fecha, producto y cliente, y difieren en la cantidad. "
                       "Ninguna se suma hasta que alguien diga cual vale.",
                raw={"codigo": code, "filas": group},
                candidates=[
                    {"valor": f"cantidad {r.get('cantidad')} por {r.get('total')}", "puntaje": 0.5, "fila": r}
                    for r in group
                ],
            )

        report.note(
            f"{len(groups)} codigos repetidos: {len(identical)} eran la misma fila cargada dos veces y se "
            f"unificaron solas, {len(conflicting)} tienen datos distintos y esperan decision"
        )
        return conflicting

    # ------------------------------------------------------------------ one row

    def _parse(self, row: dict) -> dict:
        repairs: list[str] = []
        date_result = parse_date(row.get("fecha"))
        quantity = _as_int(row.get("cantidad"))
        unit = parse_amount(row.get("precioUnit")).value
        total = parse_amount(row.get("total")).value

        product = self._store.products.by_external(row.get("productoId") or "")
        if product is None and unit is not None:
            product = self._product_by_price(unit)
            if product:
                repairs.append(
                    f"el producto {row.get('productoId')!r} no existe; por el precio unitario "
                    f"solo puede ser {product['code']}"
                )

        # exactly one hole in quantity x price = total is arithmetic, not a guess
        if quantity is None and unit and total:
            quantity, _ = divmod(total, unit)
            repairs.append(f"la cantidad venia como {row.get('cantidad')!r} y sale de dividir el total por el precio")
        elif total is None and quantity is not None and unit is not None:
            total = quantity * unit
            repairs.append("el total venia vacio y sale de multiplicar cantidad por precio")
        elif unit is None and quantity and total is not None:
            unit = total // quantity
            repairs.append("el precio unitario venia vacio y sale de dividir el total por la cantidad")

        return {
            "sold_on": date_result.value,
            "date_raw": row.get("fecha"),
            "product_id": product["id"] if product else None,
            "product_raw": row.get("productoId"),
            "customer": (row.get("cliente") or "").strip() or None,
            "quantity": quantity,
            "unit_cents": unit,
            "total_cents": total,
            "repairs": repairs,
        }

    def _verdict(self, code: str, parsed: dict, conflicting: dict[str, list[dict]]) -> tuple[str, str]:
        if code in conflicting:
            return "conflicto", "el mismo codigo aparece con cantidades distintas y nadie decidio cual vale"

        if not parsed["sold_on"]:
            self._raise_broken(code, parsed, f"la fecha {parsed['date_raw']!r} no existe")
            return "rota", f"fecha invalida: {parsed['date_raw']!r}. No se puede imputar a ningun mes."

        if parsed["quantity"] is None or parsed["unit_cents"] is None or parsed["total_cents"] is None:
            self._raise_broken(code, parsed, "faltan datos y no alcanzan para deducir el resto")
            return "rota", "faltan cantidad, precio o total y no se pueden deducir"

        # a quantity that is negative or zero is a typing slip, and it shows: the total almost
        # always matches the quantity without its sign. Naming that is more useful than
        # reporting the multiplication as off by a factor of minus one.
        if parsed["quantity"] <= 0:
            corrected = abs(parsed["quantity"])
            matches = corrected * parsed["unit_cents"] == parsed["total_cents"]
            detail = (f"la cantidad vino como {parsed['quantity']}. Con {corrected} el total cierra exacto"
                      if matches else f"la cantidad vino como {parsed['quantity']}, que no puede ser")
            self._raise_broken(code, parsed, detail,
                               proposal=corrected if matches else None, field="quantity")
            return "rota", f"cantidad invalida: {parsed['quantity']}"

        expected = parsed["quantity"] * parsed["unit_cents"]
        if expected != parsed["total_cents"]:
            factor = parsed["total_cents"] / expected
            hint = f" (el total es {factor:.0f} veces lo que deberia)" if abs(factor - round(factor)) < 0.01 and factor > 1 else ""
            self._raise_broken(
                code, parsed,
                f"cantidad por precio da {expected}, pero el total dice {parsed['total_cents']}{hint}",
                proposal=expected, field="total_cents",
            )
            return "rota", f"el total no cierra con cantidad por precio{hint}"

        return "valida", "; ".join(parsed["repairs"])

    def _raise_broken(self, code: str, parsed: dict, detail: str, proposal: int | None = None,
                      field: str = "total_cents") -> None:
        candidates = []
        if proposal is not None:
            nota = ("la cantidad sin el signo" if field == "quantity" else "cantidad por precio unitario")
            # the field travels with the proposal so whoever accepts it does not have to know
            # which column the correction belongs in
            candidates.append({"valor": proposal, "puntaje": 0.9, "nota": nota, "campo": field})
        self._review.conflict(
            kind="venta-rota",
            key=code,
            title=f"La venta {code} tiene datos que no cierran",
            detail=detail,
            raw=parsed,
            candidates=candidates,
        )

    def _product_by_price(self, unit_cents: int) -> dict | None:
        """A sale pointing at a product that does not exist, matched by its unit price.

        Only accepted when exactly one product ever had that price. Two matches means
        guessing, and guessing is what this system is built not to do.
        """
        rows = self._store.db.query(
            "SELECT DISTINCT product_id FROM price_snapshot WHERE price_cents = ? LIMIT 2", (unit_cents,)
        )
        if len(rows) != 1:
            return None
        return self._store.products.get(rows[0]["product_id"])


def _as_int(value) -> int | None:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _fingerprint(parsed: dict) -> str:
    payload = json.dumps(
        [parsed["sold_on"], parsed["product_raw"], parsed["customer"], parsed["quantity"],
         parsed["unit_cents"], parsed["total_cents"]],
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]
