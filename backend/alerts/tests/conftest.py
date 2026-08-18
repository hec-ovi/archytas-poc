"""Test setup: the box on the import path, a real SQLite in a temp folder, and fixture rows.

Every test runs against a database built by `Store.open`, not a stub, because what the rules
actually depend on is the shape of the views. Nothing leaves the machine: the notifier writes
to the local tray inside the temp folder.
"""

from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest

BACKEND = Path(__file__).resolve().parents[2]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from notify import Channel, Delivery, Notifier  # noqa: E402
from store import Store  # noqa: E402

TODAY = "2026-08-18"


def day(offset: int) -> str:
    """An ISO date `offset` days away from the fixed today the tests run on."""
    return (date.fromisoformat(TODAY) + timedelta(days=offset)).isoformat()


def outbox_lines(tmp_path: Path) -> list[dict]:
    """Every message the local tray actually wrote, one per delivery."""
    path = tmp_path / "outbox.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


class FlakyChannel(Channel):
    """Refuses the first attempts and accepts the next one, like a token being renewed."""

    name = "flaky"

    def __init__(self, fails: int = 1):
        super().__init__(("marcela",))
        self.attempts = 0
        self._fails = fails

    def send(self, recipient, message) -> Delivery:
        self.attempts += 1
        if self.attempts <= self._fails:
            return Delivery.failure(self.name, recipient, "el proveedor rechazo el envio")
        return Delivery.sent(self.name, recipient, f"flaky-{self.attempts}")


class Seed:
    """Writes fixture rows through the real repositories."""

    def __init__(self, store: Store):
        self._store = store
        self._count = 0

    def _next(self) -> int:
        self._count += 1
        return self._count

    def supplier(self, name: str = "Distribuidora Andina", slug: str = "andina") -> int:
        return self._store.suppliers.save({"slug": slug, "name": name, "cuit": "30-11111111-1", "terms_days": 30})

    def invoice(
        self,
        supplier_id: int,
        number: str,
        due_on: str,
        amount_cents: int = 5_000_000,
        paid_cents: int = 0,
        with_receipt: bool = False,
    ) -> int:
        invoice_id = self._store.invoices.save(
            {
                "external_id": f"f{self._next()}",
                "number": number,
                "supplier_id": supplier_id,
                "issued_on": day(-30),
                "due_on": due_on,
                "amount_cents": amount_cents,
            }
        )
        if paid_cents:
            self._store.payments.save(
                {
                    "reference": f"P-{number}",
                    "invoice_id": invoice_id,
                    "supplier_id": supplier_id,
                    "paid_on": day(-1),
                    "amount_cents": paid_cents,
                }
            )
        if with_receipt:
            self._store.receipts.save(
                {"number": f"REC-{number}", "invoice_id": invoice_id, "issued_on": day(-2)}
            )
        return invoice_id

    def order(
        self,
        supplier_id: int,
        number: str,
        ordered_on: str,
        status: str = "pendiente",
        estimated_cents: int = 1_200_000,
    ) -> int:
        return self._store.orders.save(
            {
                "external_id": f"o{self._next()}",
                "number": number,
                "supplier_id": supplier_id,
                "ordered_on": ordered_on,
                "quantity": 10,
                "estimated_cents": estimated_cents,
                "status": status,
            }
        )

    def message(
        self,
        supplier_id: int,
        subject: str,
        kind: str = "reclamo",
        resolved: int = 0,
        invoice_id: int | None = None,
    ) -> int:
        return self._store.messages.save(
            {
                "external_id": f"m{self._next()}",
                "received_on": day(-3),
                "sender": "cobranzas@andina.com.ar",
                "supplier_id": supplier_id,
                "subject": subject,
                "body": "Adjuntamos el detalle.",
                "invoice_id": invoice_id,
                "kind": kind,
                "resolved": resolved,
            }
        )

    def review_item(self, kind: str = "proveedor", title: str = "Nombre sin resolver") -> int:
        return self._store.reviews.raise_item(
            {"kind": kind, "dedupe_key": f"rev-{self._next()}", "title": title}
        )


@pytest.fixture
def store(tmp_path) -> Any:
    store = Store.open(str(tmp_path / "cordillera.db"))
    yield store
    store.close()


@pytest.fixture
def seed(store) -> Seed:
    return Seed(store)


@pytest.fixture
def notifier(tmp_path) -> Notifier:
    return Notifier.from_env({"NOTIFY_OUTBOX_PATH": str(tmp_path / "outbox.jsonl")})
