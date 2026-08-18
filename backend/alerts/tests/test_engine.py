"""What the engine promises: once only, everything recorded, and the retry that does not refire."""

from __future__ import annotations

from alerts import AlertEngine
from conftest import TODAY, FlakyChannel, day, outbox_lines
from notify import Notifier


def test_an_empty_database_interrupts_nobody(store, notifier):
    report = AlertEngine(store, notifier).run(today=TODAY)

    assert (report.raised, report.delivered, report.errors) == (0, 0, [])
    assert store.alerts.recent() == []


def test_an_event_is_raised_and_sent_once_across_two_runs(store, seed, notifier, tmp_path):
    supplier = seed.supplier()
    seed.invoice(supplier, "A-0001-00000020", due_on=day(-4), amount_cents=3_000_000)
    engine = AlertEngine(store, notifier)

    first = engine.run(today=TODAY)
    second = engine.run(today=TODAY)

    assert (first.raised, first.delivered) == (1, 1)
    assert (second.raised, second.repeated, second.delivered) == (0, 1, 0)
    assert store.alerts.count() == 1
    assert len(outbox_lines(tmp_path)) == 1


def test_the_message_carries_the_amount_and_the_due_date_in_words(store, seed, notifier, tmp_path):
    supplier = seed.supplier(name="Distribuidora Andina")
    seed.invoice(supplier, "A-0001-00000021", due_on=day(3), amount_cents=2_233_760)

    AlertEngine(store, notifier).run(today=TODAY)

    text = outbox_lines(tmp_path)[0]["text"]
    assert "A-0001-00000021" in text
    assert "$22.337,60" in text
    assert "21/08/2026" in text
    assert "Distribuidora Andina" in text


def test_every_delivery_attempt_is_recorded(store, seed, notifier):
    supplier = seed.supplier()
    seed.invoice(supplier, "A-0001-00000022", due_on=day(-4), amount_cents=3_000_000)

    AlertEngine(store, notifier).run(today=TODAY)

    event = store.alerts.recent()[0]
    deliveries = store.deliveries.for_event(event["id"])
    assert [(row["channel"], row["status"]) for row in deliveries] == [("outbox", "entregado")]


def test_a_failed_delivery_is_retried_without_raising_the_event_again(store, seed):
    channel = FlakyChannel()
    engine = AlertEngine(store, Notifier([channel]))
    supplier = seed.supplier()
    seed.invoice(supplier, "A-0001-00000023", due_on=day(-4), amount_cents=3_000_000)

    first = engine.run(today=TODAY)
    second = engine.run(today=TODAY)

    assert (first.raised, first.failed) == (1, 1)
    assert (second.raised, second.retried, second.delivered) == (0, 1, 1)
    assert channel.attempts == 2
    assert store.alerts.count() == 1
    assert store.deliveries.failed() == []


def test_one_invoice_gets_one_alert_per_pass(store, seed, notifier):
    supplier = seed.supplier()
    seed.invoice(supplier, "A-0001-00000024", due_on=day(2), amount_cents=90_000_000)

    report = AlertEngine(store, notifier).run(today=TODAY)

    assert [event["rule"] for event in store.alerts.recent()] == ["recibo_faltante"]
    assert report.skipped == 1


def test_the_settings_move_the_thresholds(store, seed, notifier):
    supplier = seed.supplier()
    seed.invoice(supplier, "A-0001-00000025", due_on=day(3), amount_cents=2_000_000)
    # with the defaults this invoice is a missing receipt and too small to announce
    store.settings.set_value("recibo_dias_antes", 1)
    store.settings.set_value("aviso_monto_minimo", 1_000_000)

    AlertEngine(store, notifier).run(today=TODAY)

    assert [event["rule"] for event in store.alerts.recent()] == ["factura_por_vencer"]
