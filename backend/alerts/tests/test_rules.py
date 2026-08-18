"""Each rule fires for the row it exists for, and stays quiet for the one beside it.

Every test runs the whole engine, which is how the box is actually used, and then looks at
what landed in `alert_event`.
"""

from __future__ import annotations

from alerts import AlertEngine
from conftest import TODAY, day


def raised(store, rule: str) -> list[dict]:
    return [event for event in store.alerts.recent() if event["rule"] == rule]


def test_the_receipt_rule_fires_only_for_the_invoice_that_still_has_none(store, seed, notifier):
    supplier = seed.supplier()
    without = seed.invoice(supplier, "A-0001-00000001", due_on=day(3), amount_cents=2_000_000)
    seed.invoice(supplier, "A-0001-00000002", due_on=day(3), amount_cents=2_000_000, with_receipt=True)

    AlertEngine(store, notifier).run(today=TODAY)

    events = raised(store, "recibo_faltante")
    assert [event["entity_id"] for event in events] == [without]
    assert events[0]["severity"] == "urgente"


def test_the_overdue_rule_fires_only_while_something_is_still_owed(store, seed, notifier):
    supplier = seed.supplier()
    owing = seed.invoice(supplier, "A-0001-00000010", due_on=day(-10), amount_cents=3_000_000)
    seed.invoice(
        supplier, "A-0001-00000011", due_on=day(-10), amount_cents=3_000_000, paid_cents=3_000_000
    )

    AlertEngine(store, notifier).run(today=TODAY)

    events = raised(store, "factura_vencida")
    assert [event["entity_id"] for event in events] == [owing]
    assert events[0]["severity"] == "urgente"


def test_the_due_soon_rule_only_speaks_above_the_amount_and_inside_the_window(store, seed, notifier):
    supplier = seed.supplier()
    big = seed.invoice(supplier, "A-1", due_on=day(3), amount_cents=20_000_000, with_receipt=True)
    seed.invoice(supplier, "A-2", due_on=day(3), amount_cents=500_000, with_receipt=True)
    seed.invoice(supplier, "A-3", due_on=day(40), amount_cents=20_000_000, with_receipt=True)

    AlertEngine(store, notifier).run(today=TODAY)

    assert [event["entity_id"] for event in raised(store, "factura_por_vencer")] == [big]


def test_the_order_rule_fires_for_the_old_open_one_only(store, seed, notifier):
    supplier = seed.supplier()
    forgotten = seed.order(supplier, "OC-100", ordered_on=day(-45))
    seed.order(supplier, "OC-101", ordered_on=day(-5))
    seed.order(supplier, "OC-102", ordered_on=day(-90), status="recibida")

    AlertEngine(store, notifier).run(today=TODAY)

    assert [event["entity_id"] for event in raised(store, "orden_vieja")] == [forgotten]


def test_the_claim_rule_fires_for_the_unresolved_claim_only(store, seed, notifier):
    supplier = seed.supplier()
    open_claim = seed.message(supplier, "Falta el recibo de la A-0001-00000015")
    seed.message(supplier, "Reclamo ya respondido", resolved=1)
    seed.message(supplier, "Aviso de stock", kind="stock")

    AlertEngine(store, notifier).run(today=TODAY)

    assert [event["entity_id"] for event in raised(store, "reclamo_sin_responder")] == [open_claim]


def test_the_review_queue_produces_one_digest_for_every_pending_item(store, seed, notifier):
    seed.review_item()
    seed.review_item(kind="rubro")
    seed.review_item()

    AlertEngine(store, notifier).run(today=TODAY)

    events = raised(store, "revision_pendiente")
    assert len(events) == 1
    assert "3" in events[0]["title"]
    assert "proveedor: 2" in events[0]["body"]
