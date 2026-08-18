"""Invoices, the payments against them, and the receipts issued for them.

Three things the client asked for live here:

- which invoices are settled, half paid, and untouched. The balance is never a stored
  number: it is the invoice total minus the payments actually recorded, so it cannot drift.
- how overdue something is. Also never stored, because it changes every night on its own.
- which invoices already have their receipt. The receipt is the proof the invoice was
  received and will be paid, and it can only be issued up to the due date.
"""

from __future__ import annotations

from typing import Any

from .base import Repository, decode, decode_all


class InvoiceRepository(Repository):
    table = "invoice"

    def by_external(self, external_id: str) -> dict[str, Any] | None:
        return self.get_by("external_id", external_id)

    def by_number(self, supplier_id: int, number: str) -> dict[str, Any] | None:
        return decode(
            self.db.one("SELECT * FROM invoice WHERE supplier_id = ? AND number = ?", (supplier_id, number))
        )

    def save(self, values: dict[str, Any]) -> int:
        key = ["external_id"] if values.get("external_id") else ["supplier_id", "number"]
        return self.upsert(values, key)

    def listing(self, supplier_id: int | None = None, state: str | None = None) -> list[dict[str, Any]]:
        clauses, params = ["1=1"], []
        if supplier_id:
            clauses.append("b.supplier_id = ?")
            params.append(supplier_id)
        if state:
            clauses.append("b.payment_state = ?")
            params.append(state)
        return self.db.query(
            f"""
            SELECT b.*, s.name AS supplier_name, s.slug AS supplier_slug, s.terms_days,
                   i.source_kind, i.status, i.product_id
            FROM invoice_balance b
            JOIN invoice i ON i.id = b.id
            LEFT JOIN supplier s ON s.id = b.supplier_id
            WHERE {' AND '.join(clauses)}
            ORDER BY b.due_on
            """,
            tuple(params),
        )

    def balance(self, invoice_id: int) -> dict[str, Any] | None:
        return self.db.one(
            """
            SELECT b.*, s.name AS supplier_name, s.slug AS supplier_slug, s.email AS supplier_email
            FROM invoice_balance b
            LEFT JOIN supplier s ON s.id = b.supplier_id
            WHERE b.id = ?
            """,
            (invoice_id,),
        )

    def due_between(self, start: str, end: str) -> list[dict[str, Any]]:
        return self.db.query(
            """
            SELECT b.*, s.name AS supplier_name, s.slug AS supplier_slug
            FROM invoice_balance b
            LEFT JOIN supplier s ON s.id = b.supplier_id
            WHERE b.due_on BETWEEN ? AND ?
            ORDER BY b.due_on
            """,
            (start, end),
        )

    def payment_summary(self) -> dict[str, int]:
        rows = self.db.query("SELECT payment_state, COUNT(*) AS n FROM invoice_balance GROUP BY payment_state")
        return {row["payment_state"]: row["n"] for row in rows}

    def without_receipt_due_before(self, limit_date: str) -> list[dict[str, Any]]:
        """Invoices whose receipt is still not issued and whose due date is closing in.

        This is the one the client loses money on: the receipt can only be issued up to the
        due date, and today nobody finds out until the supplier calls.
        """
        return self.db.query(
            """
            SELECT b.*, s.name AS supplier_name, s.email AS supplier_email
            FROM invoice_balance b
            LEFT JOIN supplier s ON s.id = b.supplier_id
            WHERE b.has_receipt = 0 AND b.due_on IS NOT NULL AND b.due_on <= ?
            ORDER BY b.due_on
            """,
            (limit_date,),
        )


class PaymentRepository(Repository):
    table = "payment"

    def save(self, values: dict[str, Any]) -> int:
        key = ["external_id"] if values.get("external_id") else ["id"]
        return self.upsert(values, key) if values.get("external_id") else self.insert(values)

    def for_invoice(self, invoice_id: int) -> list[dict[str, Any]]:
        return decode_all(
            self.db.query("SELECT * FROM payment WHERE invoice_id = ? ORDER BY paid_on, id", (invoice_id,))
        )

    def for_supplier(self, supplier_id: int) -> list[dict[str, Any]]:
        return decode_all(
            self.db.query(
                """
                SELECT p.*, i.number AS invoice_number
                FROM payment p
                LEFT JOIN invoice i ON i.id = p.invoice_id
                WHERE p.supplier_id = ?
                ORDER BY p.paid_on DESC, p.id DESC
                """,
                (supplier_id,),
            )
        )


class ReceiptRepository(Repository):
    table = "receipt"

    def for_invoice(self, invoice_id: int) -> dict[str, Any] | None:
        return self.get_by("invoice_id", invoice_id)

    def save(self, values: dict[str, Any]) -> int:
        return self.upsert(values, ["number"])

    @staticmethod
    def number_for(invoice_number: str) -> str:
        """A receipt is named after the invoice it acknowledges.

        Derived instead of sequential so the same invoice always produces the same receipt
        number, whether it came from a sync or from someone pressing the button.
        """
        return f"REC-{invoice_number}"
