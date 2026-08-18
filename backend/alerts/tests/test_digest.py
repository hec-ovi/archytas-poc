"""Many events, one message.

The live database holds seventy four invoices with a balance and claims going back to 2023.
All true, none of it readable as seventy four notifications, and each one costs money to
deliver. Past `aviso_maximo_por_regla` the events still get raised, but only a digest goes out.
"""

from __future__ import annotations

from alerts import AlertEngine
from .conftest import TODAY, FlakyChannel, day, outbox_lines
from notify import Notifier


def overdue_invoices(seed, count: int, supplier: int) -> None:
    """`count` invoices past due with a balance, each older and bigger than the last."""
    for number in range(count):
        seed.invoice(
            supplier,
            f"A-0001-0000{100 + number}",
            due_on=day(-10 - number),
            amount_cents=1_000_000 * (number + 1),
        )


def test_a_rule_under_the_threshold_sends_one_message_each(store, seed, notifier, tmp_path):
    overdue_invoices(seed, 5, seed.supplier())

    report = AlertEngine(store, notifier).run(today=TODAY)

    assert (report.raised, report.delivered, report.digests) == (5, 5, 0)
    assert len(outbox_lines(tmp_path)) == 5


def test_a_rule_over_the_threshold_sends_one_digest(store, seed, notifier, tmp_path):
    overdue_invoices(seed, 6, seed.supplier())

    report = AlertEngine(store, notifier).run(today=TODAY)

    assert (report.raised, report.delivered, report.digests, report.grouped) == (6, 1, 1, 6)
    assert store.alerts.count() == 6

    messages = outbox_lines(tmp_path)
    assert len(messages) == 1
    text = messages[0]["text"]
    assert "6 facturas vencidas" in text
    assert "$210.000,00" in text  # 1 + 2 + 3 + 4 + 5 + 6 millones de centavos
    assert "A-0001-0000105" in text  # la mas vieja encabeza el resumen
    assert messages[0]["template"]["name"] == "factura_vencida_resumen"


def test_the_digest_leaves_no_event_pending_for_the_retry(store, seed, notifier):
    overdue_invoices(seed, 6, seed.supplier())
    engine = AlertEngine(store, notifier)

    engine.run(today=TODAY)
    second = engine.run(today=TODAY)

    delivered = [row["status"] for event in store.alerts.recent() for row in store.deliveries.for_event(event["id"])]
    assert delivered == ["entregado"] * 6
    assert store.deliveries.failed() == []
    assert (second.retried, second.delivered, second.raised) == (0, 0, 0)


def test_a_failed_digest_is_retried_as_one_digest(store, seed):
    channel = FlakyChannel()
    engine = AlertEngine(store, Notifier([channel]))
    overdue_invoices(seed, 6, seed.supplier())

    first = engine.run(today=TODAY)
    second = engine.run(today=TODAY)

    assert (first.digests, first.failed) == (1, 1)
    assert (second.digests, second.retried, second.delivered) == (1, 6, 1)
    assert channel.attempts == 2  # dos mensajes en total, no doce
    assert store.deliveries.failed() == []


def test_the_setting_moves_where_the_digest_starts(store, seed, notifier, tmp_path):
    overdue_invoices(seed, 3, seed.supplier())
    store.settings.set_value("aviso_maximo_por_regla", 2)

    report = AlertEngine(store, notifier).run(today=TODAY)

    assert (report.raised, report.digests) == (3, 1)
    assert "3 facturas vencidas" in outbox_lines(tmp_path)[0]["text"]
