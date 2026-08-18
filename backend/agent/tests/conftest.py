"""Test setup: a real database in a temporary folder, and a model that never runs.

The store is the real one, opened on a throwaway file and seeded with the few rows every
test needs. The model is a `MockTransport` that answers whatever the test queued, so the
tool loop is exercised without llama.cpp being up.
"""

from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

import httpx
import pytest

BACKEND = Path(__file__).resolve().parents[2]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from agent import Agent, AgentSettings, ChatClient, ToolRegistry  # noqa: E402  (needs the path above)
from store import Store  # noqa: E402


def days_from_today(days: int) -> str:
    return (date.today() + timedelta(days=days)).isoformat()


class FakeModel:
    """Answers the queued replies in order, and keeps every request it received."""

    def __init__(self, replies: list[dict]):
        self._replies = list(replies)
        self.requests: list[dict] = []
        self.client = httpx.Client(transport=httpx.MockTransport(self._handle))

    def _handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(json.loads(request.content))
        reply = self._replies.pop(0) if len(self._replies) > 1 else self._replies[0]
        return httpx.Response(200, json={"choices": [{"message": reply, "finish_reason": "stop"}]})

    @staticmethod
    def says(text: str) -> dict:
        return {"role": "assistant", "content": text}

    @staticmethod
    def calls(name: str, **arguments) -> dict:
        return {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": f"call-{name}",
                    "type": "function",
                    "function": {"name": name, "arguments": json.dumps(arguments)},
                }
            ],
        }


@pytest.fixture
def store(tmp_path) -> Store:
    store = Store.open(str(tmp_path / "cordillera.db"))
    _seed(store)
    yield store
    store.close()


@pytest.fixture
def registry(store) -> ToolRegistry:
    return ToolRegistry(store)


@pytest.fixture
def agent_with(store):
    """An agent wired to a scripted model."""

    def build(replies: list[dict], max_turns: int = 4) -> tuple[Agent, FakeModel]:
        model = FakeModel(replies)
        settings = AgentSettings(base_url="http://modelo/v1", model="test", max_turns=max_turns)
        return Agent(store, settings, client=ChatClient(settings, http=model.client)), model

    return build


def _seed(store: Store) -> None:
    """Two suppliers, three invoices in the three payment states, and one of everything else."""
    cuyo = store.suppliers.save(
        {"slug": "herramientas-cuyo-srl", "name": "Herramientas Cuyo SRL", "cuit": "30-64738291-8",
         "email": "pagos@cuyo.com.ar", "terms_days": 30}
    )
    aceros = store.suppliers.save(
        {"slug": "aceros-belgrano-sa", "name": "Aceros Belgrano SA", "cuit": "30-71234567-4", "terms_days": 45}
    )

    category = store.categories.save({"slug": "ferreteria-general", "name": "Ferreteria General"})
    product = store.products.save(
        {"external_id": "p1", "code": "COR-0001", "description": "Amoladora angular",
         "category_id": category, "price_cents": 4500000, "stock": 2}
    )

    # vence en diez dias: se le puede emitir recibo
    open_invoice = store.invoices.save(
        {"number": "F-7797", "supplier_id": cuyo, "issued_on": days_from_today(-20),
         "due_on": days_from_today(10), "amount_cents": 50000000, "product_id": product}
    )
    # vencida hace un mes: el recibo ya no se puede emitir
    expired = store.invoices.save(
        {"number": "F-1000", "supplier_id": cuyo, "issued_on": days_from_today(-60),
         "due_on": days_from_today(-30), "amount_cents": 20000000}
    )
    partial = store.invoices.save(
        {"number": "F-2000", "supplier_id": aceros, "issued_on": days_from_today(-15),
         "due_on": days_from_today(15), "amount_cents": 10000000}
    )
    store.payments.insert(
        {"reference": "TRF-1", "invoice_id": partial, "supplier_id": aceros,
         "paid_on": days_from_today(-5), "amount_cents": 4000000, "created_by": "portal"}
    )
    for invoice_id in (open_invoice, expired, partial):
        invoice = store.invoices.get(invoice_id)
        store.calendar.sync_from_invoice(invoice, invoice["supplier_id"])

    store.sales.save(
        {"code": "V-1", "sold_on": days_from_today(-3), "product_id": product, "customer": "Obra Norte",
         "quantity": 2, "unit_cents": 4500000, "total_cents": 9000000, "row_hash": "h1"}
    )
    store.reviews.raise_item(
        {"kind": "proveedor", "dedupe_key": "proveedor:Herram. Cuyo", "title": "Proveedor sin identificar",
         "detail": "vino como 'Herram. Cuyo'", "raw": {"proveedor": "Herram. Cuyo"},
         "candidates": [{"valor": "herramientas-cuyo-srl", "puntaje": 0.81}]}
    )
    store.messages.save(
        {"external_id": "m1", "received_on": days_from_today(-1), "sender": "Herramientas Cuyo SRL",
         "supplier_id": cuyo, "subject": "Reclamo de pago", "body": "Falta el pago de F-7797", "kind": "reclamo"}
    )
